from dataclasses import dataclass
import os
from typing import Callable, List

from corr.correction_problem import GenericProblem
from corr.exceptions import FolderNotFound


@dataclass
class BaseCorrector:
    from_folder_path : str
    to_folder_path : str
    expected_extensions : List[str]
    correct_file_delegate : Callable[[str, str, dict[str, any]], str]

    def correct_all_files(this, args : dict[str, any] = None):
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
            
            try:
                saved_output_file_paths = this.correct_file_delegate(full_file_path, this.to_folder_path, args)
            except GenericProblem as e:
                print(f"Error correcting {file_name}: {e.get_problem}")
            
            outputs_str = ""
            for j, output_file_path in enumerate(saved_output_file_paths):
                outputs_str += output_file_path if j == 0 else f" and {output_file_path}"
            
            for saved_output_file_path in saved_output_file_paths:
                print(f"Corrected {file_name}, saved to {outputs_str} ({i + 1}/{len(files_to_correct)})")
        
        print("All done!")