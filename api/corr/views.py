from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def corr_photo(request):
    print(request.REQUEST["project-name"])
    return Response(data={"message" : "Not yet implemented!"}, status = status.HTTP_405_METHOD_NOT_ALLOWED)
