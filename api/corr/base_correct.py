from dataclasses import dataclass
import os
from typing import Callable, List

import concurrent

from corr.correction_problem import GenericProblem
from corr.exceptions import FolderNotFound

@dataclass
class CorrectTask:
    file_path : str
    to_folder_path : str
    correct_file_delegate : Callable[[str, str, dict[str, any]], str]
    args : dict[str, any]

def do_correct_task(task : CorrectTask):
    try:
        saved_output_file_paths = task.correct_file_delegate(task.file_path, task.to_folder_path, task.args)
        return f"Corrected {task.file_path}, saved to {saved_output_file_paths}"
    except GenericProblem as e:
        return f"Error correcting {task.file_path}: {e.get_problem}"
    
@dataclass
class BaseCorrector:
    from_folder_path : str
    to_folder_path : str
    expected_extensions : List[str]
    correct_file_delegate : Callable[[str, str, dict[str, any]], str]

    def correct_all_files(self, args : dict[str, any] = None):
        """Corrects all files in from_folder_path, saving the results to to_folder_path."""
        for folder in [self.from_folder_path, self.to_folder_path]:
            if not (os.path.exists(folder)):
                raise FolderNotFound(folder)
        
        num_cores = os.cpu_count() or 1
        files_to_correct = sorted(os.listdir(self.from_folder_path))

        tasks : List[CorrectTask] = []
        for file_name in files_to_correct:
            full_file_path = f"{self.from_folder_path}/{file_name}"
            split_file_name = file_name.split(".")

            if len(split_file_name) <= 1:
                print(f"{full_file_path} does not have a file extension! Skipping it!")
                continue

            file_extension = split_file_name[-1]
            if file_extension not in self.expected_extensions:
                print(f"{full_file_path}'s extension \"{file_extension}\" was not one of {self.expected_extensions})! Skipping it!")
                continue
            
            tasks.append(CorrectTask(full_file_path, self.to_folder_path, self.correct_file_delegate, args))
            
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
            futures = {executor.submit(do_correct_task, task): task for task in tasks}

            for future in concurrent.futures.as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"Task {task_id} generated an exception: {exc}")
                else:
                    print(result)







"""
        for i, file_name in enumerate(files_to_correct):
            full_file_path = f"{this.from_folder_path}/{file_name}"
            split_file_name = file_name.split(".")

            if len(split_file_name) <= 1:
                print(f"{full_file_path} does not have a file extension! Skipping it!")
                continue
            
            file_extension = split_file_name[-1]
            if file_extension not in self.expected_extensions:
                print(f"{full_file_path}'s extension \"{file_extension}\" was not one of {self.expected_extensions})! Skipping it!")
                continue
            
            try:
                saved_output_file_paths = this.correct_file_delegate(full_file_path, self.to_folder_path, args)
            except GenericProblem as e:
                print(f"Error correcting {file_name}: {e.get_problem}")
            
            outputs_str = ""
            for j, output_file_path in enumerate(saved_output_file_paths):
                outputs_str += output_file_path if j == 0 else f" and {output_file_path}"
            
            for saved_output_file_path in saved_output_file_paths:
                print(f"Corrected {file_name}, saved to {outputs_str} ({i + 1}/{len(files_to_correct)})")
        
        print("All done!")
"""