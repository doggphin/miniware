from typing import Callable, List
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mwlocal.helpers import CustomException, make_message
from corr.base_correct import BaseCorrector, CompleteCorrector
from .prints import prints_correct
from .slides import slides_correct
from .audio import audio_correct
from .video import vhs_correct

PHOTO_EXTENSIONS = ["jpg", "jpeg", "tif", "tiff"]
AUDIO_EXTENSIONS = ["mp3", "wav"]
VIDEO_EXTENSIONS = ["mp4"]

def correct(from_folder : str, to_folder : str, allowed_extensions : List[str], correct_file_delegate : Callable[[str, str], str]):
    try:
        corrector = BaseCorrector(from_folder, to_folder, allowed_extensions, correct_file_delegate)
        corrector.correct_all_files()
    except CustomException as e:
        return e.get_response()

    return Response(data=make_message("All done!"))


@api_view(['POST'])
def correct_slides(request, from_folder : str, to_folder : str):
    return correct(from_folder, to_folder, PHOTO_EXTENSIONS, slides_correct.correct_slide)


@api_view(['POST'])
def correct_prints(request, from_folder : str, to_folder : str):
    return correct(from_folder, to_folder, PHOTO_EXTENSIONS, prints_correct.correct_print)


@api_view(['POST'])
def correct_audio(request, from_folder : str, to_folder : str):
    print("requested to correct audio!")
    return correct(from_folder, to_folder, AUDIO_EXTENSIONS, audio_correct.correct_audio)


@api_view(['POST'])
def correct_vhs(request, from_folder : str, to_folder : str):
    print("requested to correct video!")
    return correct(from_folder, to_folder, VIDEO_EXTENSIONS, vhs_correct.correct_vhs)


@api_view(['POST'])
def correct_all(request, project_folder : str):
    try:
        complete_corrector = CompleteCorrector(project_folder = project_folder)
        complete_corrector.correct_everything()
    except CustomException as e:
        return e.get_response()

    return Response(data=make_message("All done!"))