from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List
from rest_framework.response import Response
from abc import ABC, abstractmethod


@dataclass
class BaseProjectInfo(ABC):
    first_name : str = ""
    last_name : str = ""
    project_name : str = ""

    def _init_base_project_from_sheet(self, name_row : List[str], project_name : str):
        self.first_name = name_row[0]
        self.last_name = name_row[1]
        self.project_name = project_name

    def get_base_project_data(self) -> Dict[str, any]:
        return {
            "first_name" : self.first_name,
            "last_name" : self.last_name,
            "project_name" : self.project_name
        }


@dataclass
class BaseMediaRow(BaseProjectInfo, ABC):
    has_corrected : bool = False
    custom_folder_name : str = ""

    def _init_base_row_from_sheet(self, corrected_column : List[str], custom_folder_name : str):
        self.has_corrected = "Y" in corrected_column
        self.custom_folder_name = custom_folder_name

    def get_correctable_row_data(self) -> Dict[str, any]:
        return {
            "has_corrected" : self.has_corrected,
            "custom_folder_name" : self.custom_folder_name
        }
    
    @abstractmethod
    def pull_from_sheet(self, spreadsheet_id : str, group_identifier : str) -> BaseMediaRow:
        pass
    
    @abstractmethod
    def to_response(self) -> Response:
        pass