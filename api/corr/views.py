from typing import Callable, List
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mwlocal.helpers import CustomException, make_message
from corr.base_correct import BaseCorrector
from corr.prints.prints_correct import correct_print
from .slides.slides_correct import correct_slide

PHOTO_EXTENSIONS = ["jpg", "jpeg", "tif", "tiff"]

def correct(from_folder : str, to_folder : str, allowed_extensions : List[str], correct_file_delegate : Callable[[str, str], str]):
    try:
        corrector = BaseCorrector(from_folder, to_folder, allowed_extensions, correct_file_delegate)
        corrector.correct_all_files()
    except CustomException as e:
        return e.get_response()

    return Response(data=make_message("All done!"))


@api_view(['POST'])
def correct_slides(request, from_folder : str, to_folder : str):
    return correct(from_folder, to_folder, PHOTO_EXTENSIONS, correct_slide)


@api_view(['POST'])
def correct_prints(request, from_folder : str, to_folder : str):
    return correct(from_folder, to_folder, PHOTO_EXTENSIONS, correct_print)