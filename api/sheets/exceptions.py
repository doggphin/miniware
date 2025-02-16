from rest_framework.response import Response
from abc import ABC, abstractmethod

class CustomException(ABC, Exception):
    @abstractmethod
    def get_response(self) -> Response:
        pass

    def _make_error_response(self, message : str, code : int) -> Response:
        return Response(
            data = {
                "message" : { message },
            },
            status = code
        )


class NoGroupFound(CustomException):
    """Args consist of the group that was not found"""
    def get_response(self) -> Response:
        return self._make_error_response(f"No group found for {self.args[0]}", 404)


class InvalidValue(CustomException):
    """Args consist of the column that had an invalid count"""
    def get_response(self) -> Response:
        return self._make_error_response(f"Invalid value in {self.args[0]} column", 500)


class GoogleSheetsError(CustomException):
    """Args consist of the stringified error returned by Google"""
    def get_response(self) -> Response:
        return self._make_error_response(f"Error from google sheets: {self.args[0]}", 404)


class UnknownException(CustomException):
    """Args consist of the stringified exception"""
    def get_response(self) -> Response:
        return self._make_error_response(f"Unhandled server error: {self.args[0]}", 500)
    

class FinalCheckError(CustomException):
    """Args consist of the stringified error"""
    def get_response(self) -> Response:
        return self._make_error_response(self.args[0], 422)
    

class MultiGroupCustomException(CustomException):
    """Args consist of a CustomException"""
    group_identifier : str

    def get_response(self) -> Response:
        return self._make_error_response(f"Error in group {self.group_identifier}: {self.args[0]}", 422)

 
class MultiGroupUnknownException(CustomException):
    """Args consist of a normal unhandled Exception"""
    group_identifier : str

    def get_response(self) -> Response:
        return self._make_error_response({"message" : f"Error in group {self.group_identifier}: {str(self.args[0])}"}, 500)