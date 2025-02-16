from __future__ import annotations

from typing import Dict, List
from rest_framework.response import Response

from fc.fc.slides import PhotoFinalCheckQuery, PhotoMediaType
from .sheets_requests import (
    SheetsRequest,
    RangeRequest
)
from dataclasses import dataclass
from .exceptions import (NoGroupFound, InvalidValue)
from .base_rows import BaseMediaRow


@dataclass
class PhotoRow(BaseMediaRow):
    dpi = 0
    photo_type = ""
    lp = 0
    hs = 0
    oshs = 0

    def _init_photo_row_from_sheet(self, row : List[str]):
        try:
            self.dpi = int(row[2])
        except:
            raise InvalidValue("DPI")
        
        self.photo_type = row[1]

        try:
            lp = row[7] + row[12] + row[17]
            self.lp = int(lp) if lp != "" else 0
        except:
            raise InvalidValue("LP")
        
        try:
            hs = row[8] + row[13] + row[18]
            self.hs = int(hs) if hs != "" else 0
        except:
            raise InvalidValue("HS")
        
        try:
            oshs = row[9]
            self.oshs = int(oshs) if oshs != "" else 0
        except:
            raise InvalidValue("OSHS")


    def init_from_received_data(self, corrected_row : List[str], group_row : List[str]):
        self._init_base_row_from_sheet(corrected_row, group_row[23])
        self._init_photo_row_from_sheet(group_row)


    def pull_from_sheet(self, spreadsheet_id : str, group_identifier : str):
        """ If sheets row is already known, specify in known_sheets_row to save a request """
        # First, find the row where this request is from
        sheets_request = SheetsRequest(
            spreadsheet_id = spreadsheet_id,
            ranges = [RangeRequest("Photo Trns", "A11", "A", 24)]   # Almost certainly padded to too many values but who cares
        )
        response = sheets_request.execute()
        if(response.response_code != 200):
            return response.make_drf_response()
        try:
            index = response.values[0].index(str(group_identifier))
        except:
            raise NoGroupFound(group_identifier)

        row_index_in_sheets = 11 + index

        sheets_request.ranges = [
            RangeRequest("Customer Info", "E6", "F6", 2),   # Client name
            RangeRequest("Photo Trns", "D", "D"),   # Corrected column
            RangeRequest("Photo Trns", f"A{row_index_in_sheets}", f"X{row_index_in_sheets}")    # Group info
        ]
        sheets_request.get_title = True
        response = sheets_request.execute()

        if(response.response_code != 200):
            return response.make_drf_response()

        self._init_base_project_from_sheet(response.values[0], response.title)
        self.init_from_received_data(response.values[1], response.values[2])
    

    def to_response(self) -> Response:
        full_data : Dict[str, any] = {}
        full_data = full_data | self.get_base_project_data()
        full_data = full_data | self.get_correctable_row_data()
        full_data = full_data | {
            "dpi" : self.dpi,
            "photo_type" : self.photo_type,
            "lp" : self.lp,
            "hs" : self.hs,
            "oshs" : self.oshs,
        }

        return Response(data={
            "message" : full_data
        })
    

    def to_final_check_query(self, group_identifier : str) -> PhotoFinalCheckQuery:
        return PhotoFinalCheckQuery(
            self.first_name,
            self.last_name,
            self.project_name,
            group_identifier,
            self.custom_folder_name,
            self.has_corrected,
            self.dpi,
            self.lp,
            self.hs,
            self.oshs,
            PhotoMediaType(self.photo_type)
        )