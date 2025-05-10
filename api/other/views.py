from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
import re
from pathlib import Path
import mimetypes
from PIL import Image
import mutagen
from mwlocal.helpers import make_message
from mwlocal.path_utils import fix_path

# File extensions to process
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.tif', '.tiff']
AUDIO_EXTENSIONS = ['.mp3', '.wav']
VIDEO_EXTENSIONS = ['.mp4']
VALID_DPI_VALUES = [300, 600, 1200, 1250, 1500, 3000, 4000, 5000]

def find_client_name_in_path(path):
    """
    Find the client name in a path by looking for the uppermost folder that contains a comma.
    
    Args:
        path: The path to search in
        
    Returns:
        Tuple of (last_name, first_initial) if found, otherwise (None, None)
    """
    # Split the path into components
    path_parts = Path(path).parts
    
    # Look for a folder name with a comma (starting from the end to find the uppermost)
    for part in reversed(path_parts):
        if ',' in part:
            # Remove any spaces and split by comma
            clean_part = part.replace(' ', '')
            name_parts = clean_part.split(',')
            
            if len(name_parts) >= 2:
                last_name = name_parts[0]
                first_name = name_parts[1].split('_')[0] if '_' in name_parts[1] else name_parts[1]
                first_initial = first_name[0] if first_name else ''
                
                return last_name, first_initial
    
    return None, None


def process_directory(dir_path, base_folder_path, problematic_files, is_subfolder=True, recursive=True, client_name=None):
    """
    Process a directory and its files, categorizing them by type.
    
    Args:
        dir_path: Path to the directory to process
        base_folder_path: Base path for relative path calculations
        problematic_files: Dictionary to collect problematic files
        is_subfolder: Whether this is a subfolder (for naming convention checks)
        recursive: Whether to process files recursively (including subdirectories)
        client_name: Optional tuple of (last_name, first_initial) to use instead of extracting from path
        
    Returns:
        Dictionary with folder data
    """
    folder_data = {}
    folder_name = os.path.basename(dir_path)
    
    # Use provided client name or find it in the path
    if client_name:
        last_name, first_initial = client_name
        is_valid_folder_name = True
    else:
        # Find client name in the path
        last_name, first_initial = find_client_name_in_path(dir_path)
        is_valid_folder_name = last_name is not None and first_initial is not None
    
    # Get files (recursively or non-recursively)
    all_files = []
    if recursive:
        # Get all files recursively
        for root, _, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
    else:
        # Get only files directly in the directory (non-recursive)
        for item in os.scandir(dir_path):
            if item.is_file():
                all_files.append(item.path)
    
    # Process files by type
    image_files = []
    audio_files = []
    video_files = []
    other_files = []
    
    for file_path in all_files:
        # Print the absolute path of the file
        abs_path = os.path.abspath(file_path)
        print(f"Processing file: {abs_path}")
        
        file_name = os.path.basename(file_path)
        _, file_ext = os.path.splitext(file_name)
        file_ext = file_ext.lower()
        
        # Check file naming convention if folder name is valid
        if is_valid_folder_name:
            expected_prefix = f"{last_name}{first_initial}_"
            if not file_name.startswith(expected_prefix):
                rel_path = os.path.relpath(file_path, base_folder_path)
                problematic_files["incorrect name"].append(rel_path)
                print(f"  - Incorrect name: {file_name} (expected prefix: {expected_prefix})")
        
        # Categorize by file type
        if file_ext in IMAGE_EXTENSIONS:
            image_files.append(file_path)
            print(f"  - Categorized as image: {file_ext}")
        elif file_ext in AUDIO_EXTENSIONS:
            audio_files.append(file_path)
            print(f"  - Categorized as audio: {file_ext}")
        elif file_ext in VIDEO_EXTENSIONS:
            video_files.append(file_path)
            print(f"  - Categorized as video: {file_ext}")
        else:
            other_files.append(file_path)
            rel_path = os.path.relpath(file_path, base_folder_path)
            problematic_files["unrecognized file type"].append(rel_path)
            print(f"  - Unrecognized file type: {file_ext}")
    
    # Process image files
    if image_files:
        folder_data["images"] = process_image_files(image_files)
    
    # Process audio files
    if audio_files:
        folder_data["audio"] = process_audio_files(audio_files)
    
    # Process video files
    if video_files:
        folder_data["video"] = process_video_files(video_files)
    
    return folder_data


def extract_folder_number(folder_name):
    """
    Extract the folder number from a folder name like "01_xyz", "1", "02", "03_test_abcd".
    
    Args:
        folder_name: The name of the folder
        
    Returns:
        The folder number as an integer, or None if no number could be extracted
    """
    # Match patterns like "01", "1", "01_xyz", etc.
    match = re.match(r'^(\d+)(?:_.*)?$', folder_name)
    if match:
        return int(match.group(1))
    return None


def find_file_number(parts):
    """
    Find the file number in a list of parts.
    
    Args:
        parts: List of parts from splitting a filename by '_'
        
    Returns:
        The file number as an integer, or None if no file number could be found
    """
    # Look for the last part that is purely numeric (may have leading zeros)
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
        
        # Check if it's a number with leading zeros
        match = re.match(r'^0*(\d+)$', part)
        if match:
            return int(match.group(1))
    
    return None


def check_file_naming_convention(file_name, last_name, first_initial, folder_number=None):
    """
    Check if a file follows the naming convention.
    
    Args:
        file_name: The name of the file (without extension)
        last_name: The last name of the client
        first_initial: The first initial of the client
        folder_number: The folder number (if in a numbered subfolder)
        
    Returns:
        Tuple of (is_valid, error_message_or_sequential_number)
        If valid, the second element is the sequential number as an integer
        If invalid, the second element is an error message
    """
    # Expected prefix is last name + first initial
    expected_prefix = f"{last_name}{first_initial}_"
    
    # Check if file name starts with the expected prefix
    if not file_name.startswith(expected_prefix):
        return False, f"File does not start with expected prefix '{expected_prefix}'"
    
    # Extract parts after the prefix
    parts_after_prefix = file_name[len(expected_prefix):].split('_')
    
    # If in a numbered subfolder, check for folder number in filename
    if folder_number is not None:
        # Check if there are enough parts for a valid filename
        if len(parts_after_prefix) < 1:
            return False, f"File name is too short"
        
        # Look for the folder number in any part of the filename
        folder_number_found = False
        for part in parts_after_prefix:
            # Check if the part is exactly the folder number
            if part.isdigit() and int(part) == folder_number:
                folder_number_found = True
                break
            
            # Check if the part starts with the folder number (with leading zeros)
            folder_number_str = str(folder_number).zfill(2)  # Handle both "1" and "01"
            if part.startswith(folder_number_str) and (len(part) == len(folder_number_str) or not part[len(folder_number_str):].isdigit()):
                folder_number_found = True
                break
        
        if not folder_number_found:
            return False, f"Folder number {folder_number} not found in filename"
    
    # Find the file number (the last purely numeric part)
    file_number = find_file_number(parts_after_prefix)
    
    if file_number is None:
        return False, f"File should have a sequential number"
    
    return True, file_number


@api_view(['POST'])
def manual_final_check(request, folder_path):
    """
    Endpoint that analyzes a folder and its immediate subdirectories for file naming conventions.
    
    The expected structure is:
    - Main folder: "LastName, FirstName_xyz_xyz"
    - Subfolders: "01_xyz", "02_xyz", "03_xyz", etc.
    
    Files in subfolders should follow the format:
    - "LastNameF_xyz_NN_SSS_xyz" where:
      - LastNameF is the last name and first initial
      - NN is the subfolder number (e.g., 01, 02)
      - SSS is a sequential number (001, 002, etc.)
      - xyz can be any text
    
    Files in the main folder (no subfolder) should follow:
    - "LastNameF_xyz_SSS_xyz"
    
    Args:
        request: The HTTP request
        folder_path: Path to the folder to analyze
        
    Returns:
        JSON response with analysis results
    """
    # Fix path for cross-platform compatibility
    folder_path = fix_path(folder_path)
    print(f"Using folder path: {folder_path}")
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        return Response(data=make_message(f"Folder not found: {folder_path}"), status=404)
    
    # Get immediate subdirectories
    try:
        subdirs = [f.path for f in os.scandir(folder_path) if f.is_dir()]
    except Exception as e:
        return Response(data=make_message(f"Error accessing folder: {str(e)}"), status=500)
    
    result = {}
    problematic_files = {
        "incorrect name": [],
        "unrecognized file type": [],
        "non-sequential numbering": []
    }
    
    # Process the main folder (non-recursively) using the original process_directory function
    main_folder_data = process_directory(folder_path, folder_path, problematic_files, is_subfolder=False, recursive=False)
    if main_folder_data:
        result["Main Folder"] = main_folder_data
    
    # Find client name in the main folder path for consistent naming across all files
    main_client_name = find_client_name_in_path(folder_path)
    last_name, first_initial = main_client_name if main_client_name[0] and main_client_name[1] else (None, None)
    
    if last_name and first_initial:
        # Check main folder files for naming convention and sequential numbering
        main_folder_files = []
        for item in os.scandir(folder_path):
            if item.is_file():
                main_folder_files.append(item.path)
        
        if main_folder_files:
            if "Main Folder" not in result:
                result["Main Folder"] = {}
            
            result["Main Folder"]["naming_convention"] = {"files": []}
            sequential_numbers = set()
            
            for file_path in main_folder_files:
                file_name = os.path.basename(file_path)
                file_name_without_ext, file_ext = os.path.splitext(file_name)
                file_ext = file_ext.lower()
                
                # Skip sequential numbering check for audio files and unrecognized file types
                if file_ext in AUDIO_EXTENSIONS or file_ext not in (IMAGE_EXTENSIONS + VIDEO_EXTENSIONS):
                    continue
                
                # Check file naming convention
                is_valid, value = check_file_naming_convention(file_name_without_ext, last_name, first_initial)
                
                if is_valid:
                    sequential_number = value
                    sequential_numbers.add(sequential_number)
                    result["Main Folder"]["naming_convention"]["files"].append({
                        "name": file_name,
                        "sequential_number": sequential_number
                    })
                else:
                    error_message = value
                    rel_path = os.path.relpath(file_path, folder_path)
                    problematic_files["incorrect name"].append(f"{rel_path} - {error_message}")
            
            # Check for non-sequential numbering
            if sequential_numbers:
                # Sort the sequential numbers
                sorted_numbers = sorted(sequential_numbers)
                file_count = len(sorted_numbers)
                
                print(f"Main folder - Sequential numbers: {sorted_numbers}")
                print(f"Main folder - File count: {file_count}")
                
                # Expected numbers should be 1 through the count of files
                expected_numbers = set(range(1, file_count + 1))
                
                # Check for missing numbers within the expected range
                missing_numbers = expected_numbers - set(sorted_numbers)
                
                # Check for numbers outside the expected range (too high)
                out_of_range_numbers = [num for num in sorted_numbers if num > file_count]
                
                print(f"Main folder - Missing numbers: {missing_numbers}")
                print(f"Main folder - Out of range numbers: {out_of_range_numbers}")
                
                # Debug: Print all files in the main folder
                print("Main folder files:")
                for file_info in result["Main Folder"]["naming_convention"]["files"]:
                    print(f"  {file_info['name']} - {file_info['sequential_number']}")
                
                if missing_numbers:
                    problematic_files["non-sequential numbering"].append(
                        f"Main folder - Missing sequential numbers: {', '.join(map(str, sorted(missing_numbers)))}"
                    )
                
                if out_of_range_numbers:
                    problematic_files["non-sequential numbering"].append(
                        f"Main folder - Unexpected high sequential numbers: {', '.join(map(str, sorted(out_of_range_numbers)))}"
                    )
                    
                    # Add each out-of-range file to the problematic files list
                    for file_info in result["Main Folder"]["naming_convention"]["files"]:
                        if file_info["sequential_number"] in out_of_range_numbers:
                            rel_path = os.path.join("Main Folder", file_info["name"])
                            problematic_files["non-sequential numbering"].append(
                                f"{rel_path} - Unexpected high sequential number: {file_info['sequential_number']}"
                            )
    
    # Process each immediate subdirectory using the original process_directory function
    for subdir in subdirs:
        folder_name = os.path.basename(subdir)
        folder_data = process_directory(subdir, folder_path, problematic_files, client_name=main_client_name)
        
        # Add folder data to result
        if folder_data:
            result[folder_name] = folder_data
        
        # Check for naming convention and sequential numbering if client name was found
        if last_name and first_initial:
            folder_number = extract_folder_number(folder_name)
            
            if folder_number is None:
                problematic_files["incorrect name"].append(f"Subfolder '{folder_name}' does not start with a number")
                continue
            
            # Get files in this subfolder
            subfolder_files = []
            for item in os.scandir(subdir):
                if item.is_file():
                    subfolder_files.append(item.path)
            
            if not subfolder_files:
                continue
            
            if folder_name not in result:
                result[folder_name] = {}
            
            result[folder_name]["naming_convention"] = {"files": []}
            sequential_numbers = set()
            
            for file_path in subfolder_files:
                file_name = os.path.basename(file_path)
                file_name_without_ext, file_ext = os.path.splitext(file_name)
                file_ext = file_ext.lower()
                
                # Skip sequential numbering check for audio files and unrecognized file types
                if file_ext in AUDIO_EXTENSIONS or file_ext not in (IMAGE_EXTENSIONS + VIDEO_EXTENSIONS):
                    continue
                
                # Check file naming convention
                is_valid, value = check_file_naming_convention(file_name_without_ext, last_name, first_initial, folder_number)
                
                if is_valid:
                    sequential_number = value
                    sequential_numbers.add(sequential_number)
                    result[folder_name]["naming_convention"]["files"].append({
                        "name": file_name,
                        "sequential_number": sequential_number
                    })
                else:
                    error_message = value
                    rel_path = os.path.relpath(file_path, folder_path)
                    problematic_files["incorrect name"].append(f"{rel_path} - {error_message}")
            
            # Check for non-sequential numbering
            if sequential_numbers:
                # Sort the sequential numbers
                sorted_numbers = sorted(sequential_numbers)
                file_count = len(sorted_numbers)
                
                print(f"Folder {folder_name} - Sequential numbers: {sorted_numbers}")
                print(f"Folder {folder_name} - File count: {file_count}")
                
                # Expected numbers should be 1 through the count of files
                expected_numbers = set(range(1, file_count + 1))
                
                # Check for missing numbers within the expected range
                missing_numbers = expected_numbers - set(sorted_numbers)
                
                # Check for numbers outside the expected range (too high)
                out_of_range_numbers = [num for num in sorted_numbers if num > file_count]
                
                print(f"Folder {folder_name} - Missing numbers: {missing_numbers}")
                print(f"Folder {folder_name} - Out of range numbers: {out_of_range_numbers}")
                
                # Debug: Print all files in this subfolder
                print(f"Folder {folder_name} files:")
                for file_info in result[folder_name]["naming_convention"]["files"]:
                    print(f"  {file_info['name']} - {file_info['sequential_number']}")
                
                if missing_numbers:
                    problematic_files["non-sequential numbering"].append(
                        f"Folder {folder_name} - Missing sequential numbers: {', '.join(map(str, sorted(missing_numbers)))}"
                    )
                
                if out_of_range_numbers:
                    problematic_files["non-sequential numbering"].append(
                        f"Folder {folder_name} - Unexpected high sequential numbers: {', '.join(map(str, sorted(out_of_range_numbers)))}"
                    )
                    
                    # Add each out-of-range file to the problematic files list
                    for file_info in result[folder_name]["naming_convention"]["files"]:
                        if file_info["sequential_number"] in out_of_range_numbers:
                            rel_path = os.path.join(folder_name, file_info["name"])
                            problematic_files["non-sequential numbering"].append(
                                f"{rel_path} - Unexpected high sequential number: {file_info['sequential_number']}"
                            )
    
    # Add problematic files to result
    result["problematic_files"] = problematic_files
    
    return Response(data=result)


def process_image_files(image_files):
    """Process image files and return statistics."""
    normal_count = 0
    handscans_count = 0
    oversized_handscans_count = 0
    dpi_values = set()
    
    for file_path in image_files:
        file_name = os.path.basename(file_path)
        
        # Categorize by name pattern
        if "_OSHS" in file_name:
            oversized_handscans_count += 1
        elif "_HS" in file_name:
            handscans_count += 1
        else:
            normal_count += 1
        
        # Check DPI
        try:
            with Image.open(file_path) as img:
                if hasattr(img, 'info') and 'dpi' in img.info:
                    dpi = img.info['dpi']
                    # Use the x-resolution as the DPI value
                    if isinstance(dpi, tuple) and len(dpi) > 0:
                        dpi_values.add(int(dpi[0]))
        except Exception:
            # If we can't read the DPI, we'll handle it below
            pass
    
    # Determine DPI status
    if len(dpi_values) == 1:
        dpi_value = next(iter(dpi_values))
        dpi_status = dpi_value if dpi_value in VALID_DPI_VALUES else f"{dpi_value} (invalid)"
    else:
        # Return all DPI values when there are multiple
        dpi_status = ", ".join(map(str, sorted(dpi_values))) if dpi_values else "unknown"
    
    return {
        "normal_count": normal_count,
        "handscans_count": handscans_count,
        "oversized_handscans_count": oversized_handscans_count,
        "dpi": dpi_status
    }


def process_audio_files(audio_files):
    """Process audio files and return statistics."""
    file_count = len(audio_files)
    total_length = 0.0
    file_types = set()
    
    for file_path in audio_files:
        _, file_ext = os.path.splitext(file_path)
        file_ext = file_ext.lower().lstrip('.')
        file_types.add(file_ext)
        
        # Get audio length
        try:
            audio = mutagen.File(file_path)
            if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                total_length += audio.info.length
        except Exception:
            # If we can't read the length, we'll just skip it
            pass
    
    return {
        "files": file_count,
        "length": round(total_length, 2),
        "fileTypes": ", ".join(sorted(file_types))
    }


def process_video_files(video_files):
    """Process video files and return statistics."""
    file_count = len(video_files)
    total_length = 0.0
    
    for file_path in video_files:
        # Get video length
        try:
            video = mutagen.File(file_path)
            if video is not None and hasattr(video, 'info') and hasattr(video.info, 'length'):
                total_length += video.info.length
        except Exception:
            # If we can't read the length, we'll just skip it
            pass
    
    return {
        "files": file_count,
        "length": round(total_length, 2)
    }


@api_view(['POST'])
def delete_files(request, folder_path):
    """
    Endpoint that deletes specified files in a folder.
    
    Args:
        request: The HTTP request with a list of file paths to delete
        folder_path: Base path for the files
        
    Returns:
        JSON response with deletion results
    """
    # Fix path for cross-platform compatibility
    folder_path = fix_path(folder_path)
    print(f"Using folder path: {folder_path}")
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        return Response(data=make_message(f"Folder not found: {folder_path}"), status=404)
    
    # Get list of files to delete from request
    file_paths = request.data.get('file_paths', [])
    if not file_paths:
        return Response(data=make_message("No files specified for deletion"), status=400)
    
    deleted_files = []
    failed_files = []
    
    # Delete each specified file
    for rel_path in file_paths:
        file_path = os.path.join(folder_path, rel_path)
        
        # Ensure the file is within the specified folder (security check)
        if not os.path.abspath(file_path).startswith(os.path.abspath(folder_path)):
            failed_files.append(f"{rel_path} (Error: Path traversal attempt detected)")
            continue
            
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(rel_path)
            else:
                failed_files.append(f"{rel_path} (Error: File not found)")
        except Exception as e:
            failed_files.append(f"{rel_path} (Error: {str(e)})")
    
    result = {
        "deleted_files": deleted_files,
        "failed_files": failed_files,
        "total_deleted": len(deleted_files),
        "total_failed": len(failed_files)
    }
    
    return Response(data=result)
