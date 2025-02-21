from dataclasses import dataclass
import os
from typing import Callable, List

from corr.exceptions import FolderNotFound


@dataclass
class BaseCorrector:
    from_folder_path : str
    to_folder_path : str
    expected_extensions : List[str]
    correct_file_delegate : Callable[[str, str], str]

    def correct_all_files(this):
        """Corrects all files in from_folder_path, saving the results to to_folder_path."""
        for folder in [this.from_folder_path, this.to_folder_path]:
            if not (os.path.exists(folder)):
                raise FolderNotFound(folder)
        
        files_to_correct = sorted(os.listdir(this.from_folder_path))
        for i, file_name in enumerate(files_to_correct):
            full_file_path = f"{this.from_folder_path}/{file_name}"
            split_file_name = file_name.split(".")

            if len(split_file_name) <= 1:
                print(f"{full_file_path} does not have a file extension! Skipping it!")
                continue
            
            file_extension = split_file_name[-1]
            if file_extension not in this.expected_extensions:
                print(f"{full_file_path}'s extension \"{file_extension}\" was not one of {this.expected_extensions})! Skipping it!")
                continue

            saved_to_path = this.correct_file_delegate(full_file_path, this.to_folder_path)
            print(f"Corrected {file_name}, saved to {saved_to_path} ({i + 1}/{len(files_to_correct)})")
        
        print("All done!")