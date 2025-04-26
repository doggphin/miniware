import io
import os
import time
import datetime
from typing import Dict, List
import librosa
import subprocess
from corr.audio.audio_correct import get_start_and_end

AUDIO_SAMPLE_RATE = 1000
CLIP_PADDING_SECONDS = 2
DEFAULT_DB_THRESHHOLD = 15

def correct_vhs(from_path : str, to_dir : str, options: Dict[str, any]) -> List[str]:
    # Start timing and record start time
    start_time = time.time()
    start_datetime = datetime.datetime.now()
    
    # Initialize options if None
    if options is None:
        options = {}
    
    # Get silence threshold option with default value
    silence_threshold_db = options.get("vhsSilenceThreshholdDb", 18)
    
    file_name, file_extension = os.path.splitext(os.path.basename(from_path))
    to_path = os.path.join(to_dir, f"{file_name}{file_extension}")
    log_path = os.path.join(to_dir, f"{file_name}_correction_log.txt")
    
    command = [
        "ffmpeg", 
        "-i", from_path, 
        "-vn",  # Disable video recording
        "-ac", "1",  # Convert to mono audio (optional)
        "-ar", str(AUDIO_SAMPLE_RATE),  # Set audio sample rate
        "-f", "wav",  # Output audio format
        "pipe:1"  # Pipe output to stdout
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("starting decode")
    audio_data, error = process.communicate()
    if process.returncode != 0:
        print(f"Error extracting audio: {error.decode('utf-8')}")
        return None
    print("done with decode")
    audio_buffer = io.BytesIO(audio_data)
    audio, sr = librosa.load(audio_buffer, sr=None)
    
    # Get the audio timing and check if it's None
    result = get_start_and_end(audio, sr, silence_threshold_db)
    if result is None:
        # No valid audio intervals found
        print(f"No valid audio intervals found in the VHS file: {from_path}")
        from corr.correction_problem import GenericProblem
        raise GenericProblem("No valid audio intervals found in the VHS file")
    
    start_audio_seconds, end_audio_seconds = result
    start_audio_seconds /= AUDIO_SAMPLE_RATE
    end_audio_seconds /= AUDIO_SAMPLE_RATE
    
    # Use only audio timing for clip boundaries
    start_seconds = max(start_audio_seconds - CLIP_PADDING_SECONDS, 0)
    end_seconds = end_audio_seconds + CLIP_PADDING_SECONDS
    
    print(f"Audio timing: {start_audio_seconds}, {end_audio_seconds}")
    print(f"Final timing: {start_seconds}, {end_seconds}")
    
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", from_path,  # Input video file
        "-ss", str(start_seconds),  # Start at second x
        "-to", str(end_seconds),  # End at second y
        "-r", "29.97",  # Enforce 29.97 FPS
        "-c:v", "libx264",  # Video codec
        "-c:a", "aac",  # Audio codec
        # "-threads", str(num_threads), # Use all available threads
        to_path  # Output file
    ], check=True)

    # End timing and record end time
    end_time = time.time()
    end_datetime = datetime.datetime.now()
    total_time = end_time - start_time
    
    # Log the information - append to file instead of overwriting
    with open(log_path, 'a') as log_file:
        log_file.write(f"\n\n========================================\n")
        log_file.write(f"VHS Correction Log - {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"========================================\n")
        log_file.write(f"File name: {os.path.basename(from_path)}\n")
        log_file.write(f"Start time: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"End time: {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Total correction time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)\n")
        log_file.write(f"Silence threshold: {silence_threshold_db} dB\n")
        log_file.write(f"Audio start time: {start_audio_seconds:.2f} seconds\n")
        log_file.write(f"Audio end time: {end_audio_seconds:.2f} seconds\n")
        log_file.write(f"Final clip start: {start_seconds:.2f} seconds\n")
        log_file.write(f"Final clip end: {end_seconds:.2f} seconds\n")
        log_file.write(f"Final clip duration: {end_seconds - start_seconds:.2f} seconds\n")
    
    print(f"VHS correction log saved to: {log_path}")
    return [to_path]

# Unused code, constants and imports:
#
# import cv2
# import numpy as np
# from typing import Optional, Tuple
#
# COLOR_DIFFERENCE_THRESHHOLD = 25
# MONOCHROME_DIFFERENCE_THRESHHOLD = 5
# BLACK_THRESHHOLD = 25
# SLOW_SPEED = 0.2
# FAST_SPEED = 30
# OUTPUT_FPS = 30
#
# def extract_frame(cap : cv2.VideoCapture, frame_idx : int) -> Tuple[bool, Optional[np.ndarray]]:
#     cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
#     ret, frame = cap.read()
#     return (ret, frame)
#
#
# def get_frame_idx_where_changed(cap : cv2.VideoCapture, start_at_frame_idx : int, increment_frames : int, skip_monochrome : bool = True) -> Optional[int]:
#     """
#     Starting at a frame, checks in increments to find when the color of the video changes significantly.
#     """
#     video_end_frame_idx = cap.get(cv2.CAP_PROP_FRAME_COUNT)
#
#     frame_idx = start_at_frame_idx
#     _, first_frame = extract_frame(cap, frame_idx)
#     last_seen_corner_colors : List[np.ndarray] = [
#         np.mean(first_frame[:16, :16], axis=(0, 1)),
#         np.mean(first_frame[:16, -16:], axis=(0, 1)),
#         np.mean(first_frame[-16:, -16:], axis=(0, 1)),
#         np.mean(first_frame[-16:, :16], axis=(0, 1))
#     ]
#     
#     while frame_idx >= 0 and frame_idx < video_end_frame_idx:
#         _, frame = extract_frame(cap, frame_idx)
#         
#         new_corner_colors : List[np.ndarray] = [
#             np.mean(frame[:16, :16], axis=(0, 1)),
#             np.mean(frame[:16, -16:], axis=(0, 1)),
#             np.mean(frame[-16:, -16:], axis=(0, 1)),
#             np.mean(frame[-16:, :16], axis=(0, 1))
#         ]
#
#         # Check all the corners. If all of them have changed color in the last frame, assume the VHS has started
#         # Multiple corners are done since different VCRs have text showing up in some corners, but seemingly never all.
#
#         is_different = False
#         differences = 0
#         for i, new_corner_color in enumerate(new_corner_colors):
#             if np.linalg.norm(last_seen_corner_colors[i] - new_corner_color) > COLOR_DIFFERENCE_THRESHHOLD:
#                 differences += 1
#         if differences == 4:        # For each corner
#             is_different = True
#         
#         # Monochrome check is used to get rid of any parts that are just static
#         # Also makes sure it isn't just a black screen
#         is_monochrome = False
#         monochromes = 0
#         if is_different and skip_monochrome:
#             for i, new_corner_color in enumerate(new_corner_colors):
#                 if (
#                     new_corner_color[0] - last_seen_corner_colors[i][1] < MONOCHROME_DIFFERENCE_THRESHHOLD and
#                     new_corner_color[1] - last_seen_corner_colors[i][2] < MONOCHROME_DIFFERENCE_THRESHHOLD and
#                     new_corner_color[2] - last_seen_corner_colors[i][0] < MONOCHROME_DIFFERENCE_THRESHHOLD and
#                     np.linalg.norm(new_corner_color) > BLACK_THRESHHOLD
#                 ):
#                     monochromes += 1
#             if monochromes == 4:        # For each corner
#                 is_different = False
#         
#         print(f"{differences} {frame_idx} {is_monochrome}")
#
#         if is_different:
#             break
#
#         last_seen_corner_colors = new_corner_colors
#         frame_idx += increment_frames
#     
#     return frame_idx
#
#
# def get_frame_idx(seconds : float, fps : float) -> int:
#     return int(seconds * fps)
#
#
# def get_seconds(frame_idx : int, fps : float) -> float:
#     return float(frame_idx / fps)
#
# # Visual processing code from original correct_vhs function:
# #    cap = cv2.VideoCapture(from_path)
# #    fps = cap.get(cv2.CAP_PROP_FPS)
# #    frames_length = cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1
# #
# #    # Watch forward slowly until the video starts
# #    start_frame_idx = get_frame_idx_where_changed(cap, 0, get_frame_idx(SLOW_SPEED, fps))
# #
# #    # Rewind really fast until the video starts
# #    end_frame_idx = get_frame_idx_where_changed(cap, frames_length, get_frame_idx(-FAST_SPEED, fps))
# #    # Then go forward a bit so it's back in the end screen, and slowly rewind until the VHS starts
# #    end_frame_idx = get_frame_idx_where_changed(
# #        cap,
# #        min(frames_length, end_frame_idx + get_frame_idx(FAST_SPEED * 2, fps)),
# #        get_frame_idx(-SLOW_SPEED, fps)
# #    )
# #
# #    start_video_seconds = get_seconds(start_frame_idx, fps)
# #    end_video_seconds = get_seconds(end_frame_idx, fps)
# #
# #    start_seconds = max(min(start_video_seconds, start_audio_seconds) - CLIP_PADDING_SECONDS, 0)
# #    end_seconds = min(max(end_video_seconds, end_audio_seconds) + CLIP_PADDING_SECONDS, get_seconds(frames_length, fps) - 0.1)
# #
# #    print(f"{start_video_seconds}, {end_video_seconds}")
# #    print(f"{start_audio_seconds}, {end_audio_seconds}")
# #    print(f"{start_seconds}, {end_seconds}")
# #    
# #    cap.release()
