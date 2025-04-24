from typing import Callable, Dict, List, Tuple, Union, Any
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os

from mwlocal.helpers import CustomException, make_message
from corr.base_correct import BaseCorrector, CompleteCorrector, SingleFileCorrector
from .prints import prints_correct
from .slides import slides_correct
from .audio import audio_correct
from .video import vhs_correct

PHOTO_EXTENSIONS = ["jpg", "jpeg", "tif", "tiff"]
AUDIO_EXTENSIONS = ["mp3", "wav"]
VIDEO_EXTENSIONS = ["mp4"]

def correct_folder(
from_folder : str,
to_folder : str,
allowed_extensions : List[str],
correct_file_delegate : Callable[[str, str, Dict[str, any]], str],
options : Dict[str, any]):
    """
    Corrects all files in a folder using the specified delegate function.
    
    Args:
        from_folder: Source folder containing files to correct
        to_folder: Destination folder for corrected files
        allowed_extensions: List of file extensions to process
        correct_file_delegate: Function to use for correcting each file
        options: Options for the correction process
        
    Returns:
        HTTP response with the result of the correction
    """
    try:
        corrector = BaseCorrector(from_folder, to_folder, allowed_extensions, correct_file_delegate, options)
        corrector.correct_all_files()
    except CustomException as e:
        return e.get_response()

    return Response(data=make_message("All done!"))


# Media type configuration map
MEDIA_CONFIG = {
    'slide': (PHOTO_EXTENSIONS, slides_correct.correct_slide),
    'print': (PHOTO_EXTENSIONS, prints_correct.correct_print),
    'audio': (AUDIO_EXTENSIONS, audio_correct.correct_audio),
    'vhs': (VIDEO_EXTENSIONS, vhs_correct.correct_vhs)
}


def get_media_config(media_type: str) -> Tuple[List[str], Callable]:
    """
    Returns the configuration for a media type.
    
    Args:
        media_type: Type of media to correct ('slide', 'print', 'audio', or 'vhs')
        
    Returns:
        Tuple containing allowed extensions and correction delegate function
    """
    if media_type not in MEDIA_CONFIG:
        raise ValueError(f"Invalid media type: {media_type}")
    
    return MEDIA_CONFIG[media_type]


def correct_folder_media(request, from_folder: str, to_folder: str, media_type: str) -> Response:
    """
    Generic function to correct all files of a specific media type in a folder.
    
    Args:
        request: The HTTP request
        from_folder: Source folder containing files to correct
        to_folder: Destination folder for corrected files
        media_type: Type of media to correct ('slide', 'print', 'audio', or 'vhs')
        
    Returns:
        HTTP response with the result of the correction
    """
    options = get_options_from_request(request)
    extensions, delegate = get_media_config(media_type)
    
    if media_type == 'audio':
        print("requested to correct audio!")
    elif media_type == 'vhs':
        print("requested to correct video!")
        
    return correct_folder(from_folder, to_folder, extensions, delegate, options)


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


def handle_single_file_correction_response(result: Tuple[bool, Union[str, Exception], Any]) -> Response:
    """
    Handles the response from a SingleFileCorrector.correct_file() call.
    
    Args:
        result: The tuple returned by SingleFileCorrector.correct_file()
            - success: Boolean indicating if the correction was successful
            - message: Success message or exception
            - output_path: Path to the corrected file if successful, None otherwise
            
    Returns:
        A Response object with the appropriate status code and message
    """
    success, message, output_path = result
    
    if success:
        return Response(data=make_message(message))
    elif isinstance(message, CustomException):
        return message.get_response()
    elif isinstance(message, FileNotFoundError):
        return Response(data=make_message(str(message)), status=404)
    elif isinstance(message, ValueError):
        return Response(data=make_message(str(message)), status=400)
    else:
        return Response(data=make_message(f"Error: {str(message)}"), status=500)


def get_options_from_request(request):
    """Extract options from request data."""
    options = {}
    if request.data and isinstance(request.data, dict) and 'options' in request.data:
        options = request.data['options']
    return options


def create_single_file_corrector(file_path: str, to_folder: str, media_type: str, options: Dict[str, any]) -> SingleFileCorrector:
    """
    Creates a SingleFileCorrector instance based on the media type.
    
    Args:
        file_path: Path to the file to correct
        to_folder: Directory to save the corrected file to
        media_type: Type of media to correct ('slide', 'print', 'audio', or 'vhs')
        options: Options for the correction process
        
    Returns:
        A SingleFileCorrector instance configured for the specified media type
    """
    extensions, delegate = get_media_config(media_type)
    
    return SingleFileCorrector(
        file_path=file_path,
        to_folder_path=to_folder,
        expected_extensions=extensions,
        correct_file_delegate=delegate,
        options=options
    )


def correct_single_media(request, file_path: str, to_folder: str, media_type: str) -> Response:
    """
    Generic function to correct a single media file.
    
    Args:
        request: The HTTP request
        file_path: Path to the file to correct
        to_folder: Directory to save the corrected file to
        media_type: Type of media to correct ('slide', 'print', 'audio', or 'vhs')
        
    Returns:
        HTTP response with the result of the correction
    """
    options = get_options_from_request(request)
    corrector = create_single_file_corrector(file_path, to_folder, media_type, options)
    return handle_single_file_correction_response(corrector.correct_file())


@api_view(['POST'])
def correct_single_slide(request, file_path: str, to_folder: str):
    return correct_single_media(request, file_path, to_folder, 'slide')


@api_view(['POST'])
def correct_single_print(request, file_path: str, to_folder: str):
    return correct_single_media(request, file_path, to_folder, 'print')


@api_view(['POST'])
def correct_single_audio(request, file_path: str, to_folder: str):
    return correct_single_media(request, file_path, to_folder, 'audio')


@api_view(['POST'])
def correct_single_vhs(request, file_path: str, to_folder: str):
    return correct_single_media(request, file_path, to_folder, 'vhs')


@api_view(['POST'])
def correct_all(request, project_folder : str):
    """
    Corrects all files in a project folder.
    
    Args:
        request: The HTTP request
        project_folder: Path to the project folder
        
    Returns:
        HTTP response with the result of the correction
    """
    print(request.body)
    try:
        options = get_options_from_request(request)
        complete_corrector = CompleteCorrector(project_folder=project_folder, options=options)
        complete_corrector.correct_everything()
    except CustomException as e:
        return e.get_response()

    return Response(data=make_message("All done!"))
