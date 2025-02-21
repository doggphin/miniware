from abc import ABC, abstractmethod
import json
from requests import Response

with open("names_to_drives.json", 'r') as file:
    NAMES_TO_DRIVES = json.load(file)


def make_message(message : str):
    return { "message" : message }


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