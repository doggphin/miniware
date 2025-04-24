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


def process_directory(dir_path, base_folder_path, problematic_files, is_subfolder=True, recursive=True):
    """
    Process a directory and its files, categorizing them by type.
    
    Args:
        dir_path: Path to the directory to process
        base_folder_path: Base path for relative path calculations
        problematic_files: Dictionary to collect problematic files
        is_subfolder: Whether this is a subfolder (for naming convention checks)
        recursive: Whether to process files recursively (including subdirectories)
        
    Returns:
        Dictionary with folder data
    """
    folder_data = {}
    folder_name = os.path.basename(dir_path)
    
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


@api_view(['POST'])
def manual_final_check(request, folder_path):
    """
    Endpoint that analyzes a folder and its immediate subdirectories for media files.
    
    Args:
        request: The HTTP request
        folder_path: Path to the folder to analyze
        
    Returns:
        JSON response with analysis results
    """
    # Check if folder exists
    if not os.path.exists(folder_path):
        return Response(data=make_message(f"Folder not found: {folder_path}"), status=404)
    
    # Get immediate subdirectories
    try:
        subdirs = [f.path for f in os.scandir(folder_path) if f.is_dir()]
        
        # Check if both "Raw" and "Corrected" folders exist
        subdir_names = [os.path.basename(d) for d in subdirs]
        if "Raw" in subdir_names and "Corrected" in subdir_names:
            # Filter out the "Raw" folder
            print(f"Found both 'Raw' and 'Corrected' folders. Skipping 'Raw' folder.")
            subdirs = [d for d in subdirs if os.path.basename(d) != "Raw"]
    except Exception as e:
        return Response(data=make_message(f"Error accessing folder: {str(e)}"), status=500)
    
    result = {}
    problematic_files = {
        "incorrect name": [],
        "unrecognized file type": []
    }
    
    # Process the main folder (non-recursively)
    main_folder_data = process_directory(folder_path, folder_path, problematic_files, is_subfolder=False, recursive=False)
    if main_folder_data:
        result["Main Folder"] = main_folder_data
    
    # Process each immediate subdirectory
    for subdir in subdirs:
        folder_name = os.path.basename(subdir)
        folder_data = process_directory(subdir, folder_path, problematic_files)
        
        # Add folder data to result
        if folder_data:
            result[folder_name] = folder_data
    
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
