from dataclasses import dataclass
import os
from typing import List

from mwlocal.helpers import NAMES_TO_DRIVES

@dataclass
class BaseProjectInfo:
    client_first_name : str
    client_last_name : str
    formatted_project_name : str

    def get_base_project_folder(self) -> str:
        folder = os.path.join(f"{NAMES_TO_DRIVES[self.formatted_project_name[0].upper()]}:\\", self.formatted_project_name)
        return folder


@dataclass
class BaseGroupInfo(BaseProjectInfo):
    group_identifier : str
    custom_group_name : str
    is_corrected : bool

    def get_media_folder(self) -> str:
        # Start with base folder
        folder = self.get_base_project_folder()
        
        # Go into "Corrected" or "Raw" if corrected is specified
        if(self.is_corrected):
            folder = os.path.join(folder, "Corrected")

        # Go into group folder
        if(self.group_identifier is not None):
            group_name = str(self.group_identifier) if self.custom_group_name == None else f"{self.group_identifier}_{self.custom_group_name}"
            folder = os.path.join(folder, group_name)

        return folder
    
    
    def get_media_file_paths(self, media_type : str) -> List[str]:
        folder = self.get_media_folder()

        if not os.path.exists(folder):
            raise Exception(f"Could not find containing folder \'{folder}\'")
        
        file_names : List[str] = []
        for (_, _, found_file_names) in os.walk(folder):
            file_names.extend(found_file_names)
            # Don't try to look into deeper folders
            break

        return file_names