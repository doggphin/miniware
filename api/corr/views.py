from typing import Callable, Dict, List, Tuple, Union, Any
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
import json

from mwlocal.helpers import CustomException, make_message
from corr.base_correct import BaseCorrector, CompleteCorrector, SingleFileCorrector
from .models import CorrectionTask
from .tasks import create_correction_task

PHOTO_EXTENSIONS = ["jpg", "jpeg", "tif", "tiff"]
AUDIO_EXTENSIONS = ["mp3", "wav"]
VIDEO_EXTENSIONS = ["mp4"]

# Media type configuration map
MEDIA_CONFIG = {
    'slide': (PHOTO_EXTENSIONS),
    'print': (PHOTO_EXTENSIONS),
    'audio': (AUDIO_EXTENSIONS),
    'vhs': (VIDEO_EXTENSIONS)
}

def get_options_from_request(request):
    """Extract options from request data."""
    options = {}
    if request.data and isinstance(request.data, dict) and 'options' in request.data:
        options = request.data['options']
    return options

def get_media_extensions(media_type: str) -> List[str]:
    """
    Returns the allowed extensions for a media type.
    
    Args:
        media_type: Type of media to correct ('slide', 'print', 'audio', or 'vhs')
        
    Returns:
        List of allowed file extensions
    """
    if media_type not in MEDIA_CONFIG:
        raise ValueError(f"Invalid media type: {media_type}")
    
    return MEDIA_CONFIG[media_type]

def correct_folder_media(request, from_folder: str, to_folder: str, media_type: str) -> Response:
    """
    Generic function to create tasks for all files of a specific media type in a folder.
    
    Args:
        request: The HTTP request
        from_folder: Source folder containing files to correct
        to_folder: Destination folder for corrected files
        media_type: Type of media to correct ('slide', 'print', 'audio', or 'vhs')
        
    Returns:
        HTTP response with the task IDs
    """
    try:
        # Validate folders
        if not os.path.exists(from_folder):
            return Response(data=make_message(f"Source folder not found: {from_folder}"), status=404)
        
        if not os.path.exists(to_folder):
            os.makedirs(to_folder, exist_ok=True)
        
        # Get files to process
        allowed_extensions = get_media_extensions(media_type)
        options = get_options_from_request(request)
        
        task_ids = []
        files_to_correct = sorted(os.listdir(from_folder))
        
        for file_name in files_to_correct:
            full_file_path = f"{from_folder}/{file_name}"
            
            # Skip directories
            if os.path.isdir(full_file_path):
                continue
                
            # Check file extension
            file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""
            if not file_extension or file_extension not in allowed_extensions:
                continue
            
            # Create task for this file
            task_id = create_correction_task(media_type, full_file_path, to_folder, options)
            task_ids.append(task_id)
        
        return Response(data={
            "message": f"Created {len(task_ids)} correction tasks",
            "task_ids": task_ids
        })
    except Exception as e:
        return Response(data=make_message(f"Error: {str(e)}"), status=500)

@api_view(['POST'])
def correct_slides(request, from_folder : str, to_folder : str):
    return correct_folder_media(request, from_folder, to_folder, 'slide')

@api_view(['POST'])
def correct_prints(request, from_folder : str, to_folder : str):
    return correct_folder_media(request, from_folder, to_folder, 'print')

@api_view(['POST'])
def correct_audio(request, from_folder : str, to_folder : str):
    return correct_folder_media(request, from_folder, to_folder, 'audio')

@api_view(['POST'])
def correct_vhs(request, from_folder : str, to_folder : str):
    return correct_folder_media(request, from_folder, to_folder, 'vhs')

@api_view(['POST'])
def correct_all(request, project_folder : str):
    """
    Creates correction tasks for all files in a project folder.
    
    Args:
        request: The HTTP request
        project_folder: Path to the project folder
        
    Returns:
        HTTP response with the task IDs
    """
    try:
        if not os.path.exists(project_folder):
            return Response(data=make_message(f"Project folder not found: {project_folder}"), status=404)
        
        raw_folder = os.path.join(project_folder, "Raw")
        if not os.path.exists(raw_folder):
            return Response(data=make_message(f"Raw folder not found in project: {raw_folder}"), status=404)
        
        options = get_options_from_request(request)
        task_ids = []
        
        # Process all subdirectories in Raw folder
        for root, dirs, files in os.walk(raw_folder):
            # Create corresponding output directory
            rel_path = os.path.relpath(root, raw_folder)
            if rel_path == '.':
                output_dir = os.path.join(project_folder, "Corrected")
            else:
                output_dir = os.path.join(project_folder, "Corrected", rel_path)
            
            os.makedirs(output_dir, exist_ok=True)
            
            # Process files in this directory
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_name_lower = file_name.lower()
                file_extension = file_name.split(".")[-1].lower() if "." in file_name else ""
                
                # Determine media type
                media_type = None
                if file_extension in AUDIO_EXTENSIONS:
                    media_type = 'audio'
                elif file_extension in PHOTO_EXTENSIONS:
                    if "_prints_" in file_name_lower:
                        media_type = 'print'
                    elif "_slides_" in file_name_lower:
                        media_type = 'slide'
                elif file_extension in VIDEO_EXTENSIONS:
                    media_type = 'vhs'
                
                if media_type:
                    task_id = create_correction_task(media_type, file_path, output_dir, options)
                    task_ids.append(task_id)
        
        return Response(data={
            "message": f"Created {len(task_ids)} correction tasks",
            "task_ids": task_ids
        })
    except Exception as e:
        return Response(data=make_message(f"Error: {str(e)}"), status=500)

@api_view(['GET', 'POST'])
def get_task_status(request, task_id):
    """
    Get or update the status of a correction task.
    
    Args:
        request: The HTTP request
        task_id: The ID of the task to check or update
        
    Returns:
        HTTP response with the task status
    """
    try:
        task = CorrectionTask.objects.get(task_id=task_id)
        
        # Handle POST request to update task status
        if request.method == 'POST':
            if 'status' in request.data:
                task.status = request.data['status']
            
            if 'result' in request.data:
                task.result = request.data['result']
                
            if 'error_message' in request.data:
                task.error_message = request.data['error_message']
                
            task.save()
        
        # Return task data for both GET and POST
        response_data = {
            "task_id": task.task_id,
            "media_type": task.media_type,
            "status": task.status,
            "file_path": task.file_path,
            "to_folder": task.to_folder,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        if task.status == 'COMPLETED':
            response_data["result"] = task.result
        elif task.status == 'FAILED':
            response_data["error_message"] = task.error_message
            
        return Response(data=response_data)
    except CorrectionTask.DoesNotExist:
        return Response(data=make_message(f"Task not found: {task_id}"), status=404)
    except Exception as e:
        return Response(data=make_message(f"Error: {str(e)}"), status=500)

@api_view(['GET'])
def get_all_tasks(request):
    """
    Get all correction tasks.
    
    Args:
        request: The HTTP request
        
    Returns:
        HTTP response with all tasks
    """
    try:
        tasks = CorrectionTask.objects.all().order_by('-created_at')
        
        response_data = []
        for task in tasks:
            task_data = {
                "task_id": task.task_id,
                "media_type": task.media_type,
                "status": task.status,
                "file_path": task.file_path,
                "created_at": task.created_at,
                "updated_at": task.updated_at
            }
            response_data.append(task_data)
            
        return Response(data=response_data)
    except Exception as e:
        return Response(data=make_message(f"Error: {str(e)}"), status=500)
