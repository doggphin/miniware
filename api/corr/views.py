import os
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from mwlocal.helpers import make_message
from .slides.correct import correct_all_slides_in_folder

@api_view(['POST'])
def correct_slides(request, from_folder : str, to_folder : str):
    print("asdf")
    
    for folder in [from_folder, to_folder]:
        if not (os.path.exists(folder)):
            return Response(data=make_message(f"Could not find {folder}!"), status=404)

    correct_all_slides_in_folder(from_folder, to_folder)

    return Response(data=make_message("All done!"))

    #return Response(data={"message" : "Not yet implemented!"}, status = status.HTTP_405_METHOD_NOT_ALLOWED)
