from rest_framework.response import Response
from mwlocal.helpers import CustomException


class FolderNotFound(CustomException):
    """Args consist of the folder that was not found"""
    def get_response(self) -> Response:
        return self._make_error_response(f"No folder with the path {self.args[0]} could be found", 404)