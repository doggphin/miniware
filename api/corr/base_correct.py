from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Callable, Dict, List, Union, Tuple

import concurrent

from corr.correction_problem import GenericProblem
from corr.exceptions import FolderNotFound, NoRawFolderToCorrectFrom
from mwlocal.helpers import CustomException
from corr.audio.audio_correct import correct_audio
from corr.prints.prints_correct import correct_print
from corr.slides.slides_correct import correct_slide
from corr.video.vhs_correct import correct_vhs

@dataclass
class CorrectTask:
    file_path : str
    to_folder_path : str
    correct_file_delegate : Callable[[str, str, Dict[str, any]], str]
    options : Dict[str, any]


def do_correct_task(task : CorrectTask):
    try:
        saved_output_file_paths = task.correct_file_delegate(task.file_path, task.to_folder_path, task.options)
        return f"Corrected {task.file_path}, saved to {saved_output_file_paths}"
    except GenericProblem as e:
        return f"Error correcting {task.file_path}: {e.get_problem}"


@dataclass
class BaseCorrector:
    from_folder_path : str
    to_folder_path : str
    expected_extensions : List[str]
    correct_file_delegate : Callable[[str, str, Dict[str, any]], str]
    options : Dict[str, any]

    def correct_all_files(self):
        """Corrects all files in from_folder_path, saving the results to to_folder_path."""

        for folder in [self.from_folder_path, self.to_folder_path]:
            if not (os.path.exists(folder)):
                raise FolderNotFound(folder)
        
        num_cores = os.cpu_count() or 1
        files_to_correct = sorted(os.listdir(self.from_folder_path))

        tasks : List[CorrectTask] = []
        for file_name in files_to_correct:
            full_file_path = os.path.join(self.from_folder_path, file_name)
            split_file_name = file_name.split(".")

            if len(split_file_name) <= 1:
                print(f"{full_file_path} does not have a file extension! Skipping it!")
                continue

            file_extension = split_file_name[-1]
            if file_extension not in self.expected_extensions:
                print(f"{full_file_path}'s extension \"{file_extension}\" was not one of {self.expected_extensions})! Skipping it!")
                continue
            
            tasks.append(CorrectTask(full_file_path, self.to_folder_path, self.correct_file_delegate, self.options))
            
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


@dataclass
class CompleteCorrectTask:
    file_path : str
    to_folder : str
    correct_file_delegate : Callable[[str, str, Dict[str, any]], str]
    options : Dict[str, any]


def do_complete_correct_task(task : CompleteCorrectTask):
    try:
        saved_output_file_paths = task.correct_file_delegate(task.file_path, task.to_folder, task.options)
        return f"Corrected {task.file_path}, saved to {saved_output_file_paths}"
    except GenericProblem as e:
        return f"Error correcting {task.file_path}: {e.get_problem}"


@dataclass
class SingleFileCorrector:
    file_path: str
    to_folder_path: str
    expected_extensions: List[str]
    correct_file_delegate: Callable[[str, str, Dict[str, any]], str]
    options: Dict[str, any] = field(default_factory=dict)
    
    def correct_file(self) -> Tuple[bool, Union[str, Exception], Union[str, None]]:
        """
        Corrects a single file and returns the result.
        
        Returns:
            Tuple containing:
            - success: Boolean indicating if the correction was successful
            - message: Success message or exception
            - output_path: Path to the corrected file if successful, None otherwise
        """
        try:
            # Check if file exists
            if not os.path.exists(self.file_path):
                return False, FileNotFoundError(f"File not found: {self.file_path}"), None
            
            # Check file extension
            file_extension = self.file_path.split('.')[-1].lower()
            if file_extension not in self.expected_extensions:
                return False, ValueError(f"Invalid file extension: {file_extension}. Expected one of {self.expected_extensions}"), None
            
            # Ensure output directory exists
            if not os.path.exists(self.to_folder_path):
                os.makedirs(self.to_folder_path, exist_ok=True)
            
            # Correct the file
            output_path = self.correct_file_delegate(self.file_path, self.to_folder_path, self.options)
            
            return True, f"File corrected successfully: {output_path}", output_path
        except CustomException as e:
            return False, e, None
        except Exception as e:
            return False, e, None

@dataclass
class CompleteCorrector:
    project_folder : str
    options : Dict[str, any] = field(default_factory=dict)

    def correct_everything(self):
        try:       
            folders = os.listdir(self.project_folder)
        except Exception as e:
            print(f"{self.project_folder} doenst exist")
            raise FolderNotFound(self.project_folder)
        
        if "Raw" not in folders:
            raise NoRawFolderToCorrectFrom()
        
        raw_folder_abs_dir = os.path.join(self.project_folder, "Raw")
        
        abs_raw_subdirs = [str(f.absolute()) for f in Path(raw_folder_abs_dir).iterdir() if f.is_dir()] + [raw_folder_abs_dir]
        print(abs_raw_subdirs)
        
        tasks : List[CompleteCorrectTask] = []
        for abs_raw_subdir in abs_raw_subdirs:
            # Use platform-agnostic path handling
            raw_path = Path(abs_raw_subdir)
            raw_parent = raw_path.parent
            raw_name = raw_path.name
            
            # Handle both cases: if we're in the Raw directory itself or in a subdirectory
            if raw_name == "Raw":
                abs_corr_folder = str(raw_parent / "Corrected")
            else:
                # For subdirectories within Raw
                raw_grandparent = raw_parent.parent
                if raw_parent.name == "Raw":
                    abs_corr_folder = str(raw_grandparent / "Corrected" / raw_name)
                else:
                    # Fallback for other cases
                    abs_corr_folder = str(raw_path).replace(os.path.join("Raw", ""), os.path.join("Corrected", ""))
                    abs_corr_folder = abs_corr_folder.replace("Raw", "Corrected")
            Path(abs_corr_folder).mkdir(parents = True, exist_ok = True)
            abs_file_paths = [str(f.absolute()) for f in Path(abs_raw_subdir).iterdir() if f.is_file()]

            for abs_file_path in abs_file_paths:
                file_name, file_extension = os.path.splitext(os.path.basename(abs_file_path))

                correct_file_delegate : Callable[[str, str, Dict[str, any]], str] = None

                # Convert the file extension and naming of the file into 
                file_name_lower = file_name.lower()
                if file_extension == ".wav" or file_extension == ".mp3":
                    correct_file_delegate = correct_audio
                elif file_extension == ".png" or file_extension == ".jpg" or file_extension == ".jpeg" or file_extension == ".tif":
                    if "_prints_" in file_name_lower:
                        correct_file_delegate = correct_print
                    elif "_slides_" in file_name_lower:
                        correct_file_delegate = correct_slide
                elif file_extension == ".mp4":
                    correct_file_delegate = correct_vhs

                if correct_file_delegate != None:
                    task = CompleteCorrectTask(
                        abs_file_path,
                        abs_corr_folder,
                        correct_file_delegate,
                        self.options
                    )
                    tasks.append(task)
        
        num_cores = os.cpu_count() or 1
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
            futures = {executor.submit(do_complete_correct_task, task): task for task in tasks}

            for future in concurrent.futures.as_completed(futures):
                task_id = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"Task {task_id} generated an exception: {exc}")
                else:
                    print(result)
