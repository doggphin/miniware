import os.path
from typing import List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dataclasses import dataclass
from rest_framework.response import Response

from sheets.exceptions import GoogleSheetsError, UnknownException

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


@dataclass
class SheetsResponse:
    values : List[List[str]]
    title : str
    response_code : int = 200
    response_error : str = None

    def make_drf_response(self) -> Response:
        response = Response(status = self.response_code)
        if(self.response_code != 200):
            response.data = {"message" : self.response_error}
        
        return response


@dataclass
class RangeRequest:
    tab_name : str
    from_cell : str
    to_cell : str
    pad_to_amount : int = None

    def gen_sheets_range(self):
        return f"'{self.tab_name}'!{self.from_cell}:{self.to_cell}"



@dataclass
class SheetsRequest:
    spreadsheet_id : str
    ranges : List[RangeRequest]
    get_title : bool = False
    service = None

    def get_service(self):
        if self.service != None:
            return

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("sheets", "v4", credentials=creds)


    def execute(self) -> SheetsResponse:
        try:
            self.get_service()

            # Convert RangeRequests into formatted sheets API request strings
            converted_ranges : List[str] = []
            for unconverted_range in self.ranges:
                converted_ranges.append(unconverted_range.gen_sheets_range())
            
            # Make the request
            result = self.service.spreadsheets().values().batchGet(
                spreadsheetId = self.spreadsheet_id,
                ranges = converted_ranges
            ).execute()
            
            # Build up ranges to return
            ranges : List[str] = []
            for i, value_range in enumerate(result["valueRanges"]):
                range = []

                for row in value_range["values"]:
                    for val in row:
                        range.append(val)

                pad_to_amount = self.ranges[i].pad_to_amount
                if pad_to_amount != None:
                    range += [""] * max(pad_to_amount - len(range), 0)

                ranges.append(range)

            title = None
            if self.get_title:
                title = self.execute_title()
            
            return SheetsResponse(
                values = ranges,
                title = title
            )

        except HttpError as error:
            raise GoogleSheetsError(str(error))

        except Exception as error:
            raise UnknownException(str(error))


    def execute_title(self) -> str:
        self.get_service()

        try:
            result = self.service.spreadsheets().get(
                spreadsheetId = self.spreadsheet_id,
                fields = "properties(title)"
            ).execute()

            return result.get("properties", {}).get("title", "N/A")
        
        except HttpError as error:
            raise GoogleSheetsError(str(error))