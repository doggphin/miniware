from dataclasses import dataclass
from enum import Enum
import os
import re
from functools import reduce
from PIL import Image

from .base import BaseGroupInfo
from sheets.exceptions import (FinalCheckError)


class PhotoMediaType(Enum):
    SLIDES = "Slides"
    PRINTS = "Prints"
    NEGS = "Negs"

class PhotoScanType(Enum):
    REGULAR = "Regular"
    HANDSCAN = "HS"
    OVERSIZED = "OSHS"

def name_to_photo_scan_type(name : str) -> PhotoScanType:
    match name:
        case "":
            return PhotoScanType.REGULAR
        case "LP":
            return PhotoScanType.REGULAR
        case "HS":
            return PhotoScanType.HANDSCAN
        case "OSHS":
            return PhotoScanType.OVERSIZED
        case "OHS":
            return PhotoScanType.OVERSIZED
        case _:
            return None


ALLOWED_SCAN_TYPES = {
    PhotoMediaType.SLIDES : [PhotoScanType.REGULAR, PhotoScanType.HANDSCAN],
    PhotoMediaType.PRINTS : [PhotoScanType.REGULAR, PhotoScanType.HANDSCAN, PhotoScanType.OVERSIZED],
    PhotoMediaType.NEGS :   [PhotoScanType.REGULAR, PhotoScanType.HANDSCAN]
}

@dataclass
class PhotoFinalCheckQuery(BaseGroupInfo):
    dpi : int
    count_reg : int
    count_hs : int
    count_oshs : int
    media_type : PhotoMediaType
    # is_tif : bool
    
    
    def raise_exception(self,
    expected : any,
    found : any,
    field_name : str,
    file_name : str):
        raise FinalCheckError(f"Incorrect {field_name} in {file_name}: Expected {expected}, found {found}")
    

    def raise_exception_if_nequal(self,
    expected : any,
    found : any,
    field_name : str):
        if(expected != found):
            raise FinalCheckError(f"Incorrect {field_name}: Expected {expected}, found {found}")


    def raise_exception_if_nequal_file(self,
    expected : any,
    found : any,
    field_name : str,
    file_name : str):
        if(expected != found):
            self.raise_exception(expected, found, field_name, file_name)


    def final_check(self):
        split_project_name = self.formatted_project_name.split("_")
        fixed_project_name = f"{split_project_name[0]}_Photo_{split_project_name[2]}"
        self.formatted_project_name = fixed_project_name

        file_names = self.get_media_file_paths(self.is_corrected)

        counts = {
            PhotoScanType.REGULAR : 0,
            PhotoScanType.HANDSCAN : 0,
            PhotoScanType.OVERSIZED : 0
        }

        seen_index_numbers = []
        for file_name in file_names:
            # Split the file name on _'s to read each part
            split = re.split(r"[.|_]", file_name)
            
            split_len = len(split)
            
            # File names should only ever include either 5 (if including scan type) or 6 (if implying it's a regular scan) split strings
            if split_len != 5 and split_len != 6:
                self.raise_exception("<name>_<media>_<group number>_<index number>_<optional scan format>.<file extension>", file_name, "name format", file_name)
            
            split_i = 0

            # Make sure the name is correct
            expected_name = f"{self.client_last_name}{self.client_first_name[0]}"
            self.raise_exception_if_nequal_file(expected_name, split[split_i], "client name", file_name)
            split_i += 1
            
            # Make sure the media type is correct
            self.raise_exception_if_nequal_file(self.media_type.value, split[split_i], "media type", file_name)
            split_i += 1
            
            # Make sure group identifier is correct
            if(self.group_identifier is not None):
                # Split into number and letter, then check both
                number_letter_splitter = r"(\d+)([A-Za-z]*)$"
                expected_match = re.match(number_letter_splitter, self.group_identifier)
                found_match = re.match(number_letter_splitter, split[split_i])
                
                expected_number = expected_match[1]
                expected_number = int(expected_number) if expected_number != "" else 0
                found_number = expected_match[1]
                found_number = int(found_number) if found_number != "" else 0

                if ((expected_match == None) != (found_match == None)) or (expected_match[2] != found_match[2]) or (expected_number != found_number):
                    self.raise_exception(self.group_identifier, split[split_i], "group identifier", file_name)
            split_i += 1
            
            # Add index number to the list to check later
            seen_index_numbers.append(int(split[split_i]))
            split_i += 1

            # If the file name was long enough to indicate it includes the scan type, check it
            photo_scan_type : PhotoScanType
            is_photo_scan_type_in_name = split_len == 6
            if is_photo_scan_type_in_name:
                photo_scan_type = name_to_photo_scan_type(split[split_i])
            else:
                photo_scan_type = PhotoScanType.REGULAR
            if(not photo_scan_type in ALLOWED_SCAN_TYPES[self.media_type]):
                # The [2:] removes the first ", "
                allowed_types_names = reduce(lambda list, scan_type: f"{list}, {scan_type.value}", ALLOWED_SCAN_TYPES[self.media_type])[2:]
                self.raise_exception(allowed_types_names, photo_scan_type if photo_scan_type is not None else split[split_i], "scan_type", file_name)
            counts[photo_scan_type] += 1
            split_i += 1
            
            # Check that the extension is jpg or tif
            if split_len == 6:
                if split[split_i] != "jpg" and split[split_i] != "tif":
                    self.raise_exception("tif or jpg", split[split_i], "file extension", file_name)
            
            # Check that the DPI is correct
            img_path = os.path.join(self.get_media_folder(), file_name)
            img = Image.open(img_path)
            img_dpi = img.info.get("dpi", (None, None))[0]
            self.raise_exception_if_nequal_file(self.dpi, img_dpi, "dpi", file_name)
        
        # Make sure all index numbers are in order
        seen_index_numbers.sort()
        last_seen_index_number = 0
        for index_number in seen_index_numbers:
            if index_number == last_seen_index_number:
                raise FinalCheckError(f"Two files have the group number {last_seen_index_number}!")
            if index_number != last_seen_index_number + 1:
                raise FinalCheckError(f"Did not find an index number for {last_seen_index_number + 1}!")
            last_seen_index_number = index_number

        # Make sure media counts are correct
        self.raise_exception_if_nequal(self.count_reg, counts[PhotoScanType.REGULAR], "regular scanned photos")
        self.raise_exception_if_nequal(self.count_hs, counts[PhotoScanType.HANDSCAN], "handscanned photos")
        self.raise_exception_if_nequal(self.count_oshs, counts[PhotoScanType.OVERSIZED], "oversized handscanned photos")