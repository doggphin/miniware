import av
import numpy as np
import subprocess

def detect_uniform_sections(video_path, threshold_ratio=1.5, confirm_frames=5):
    # Open the video file with PyAV
    container = av.open(video_path)
    stream = container.streams.video[0]
    stream.thread_type = "AUTO"  # Enable multi-threading

    variances = []
    timestamps = []

    # Iterate through frames and compute variance
    for frame in container.decode(stream):
        img = frame.to_image().convert('L')  # Convert to grayscale
        np_img = np.array(img)
        variances.append(np.var(np_img))
        timestamps.append(frame.time)  # Timestamp in seconds

    container.close()

    if not variances:
        raise ValueError("No frames read from the video.")

    # Determine threshold (using max variance from initial/final 10 frames)
    initial_sample = variances[:10] if len(variances) >= 10 else variances
    final_sample = variances[-10:] if len(variances) >= 10 else variances
    max_initial = max(initial_sample)
    max_final = max(final_sample)
    threshold = max(max_initial, max_final) * threshold_ratio

    # Find start time (first frame where variance exceeds threshold)
    start_time = 0
    for i in range(len(variances) - confirm_frames):
        if variances[i] > threshold:
            if all(v > threshold for v in variances[i+1:i+1+confirm_frames]):
                start_time = timestamps[i]
                break

    # Find end time (last frame where variance exceeds threshold)
    end_time = timestamps[-1]
    for i in reversed(range(len(variances))):
        if variances[i] > threshold:
            if all(v > threshold for v in variances[i-confirm_frames:i]):
                end_time = timestamps[i]
                break

    return start_time, end_time

def trim_and_convert_to_cfr(input_path, output_path, start_time, end_time, target_fps=30):
    # Use FFmpeg to trim and enforce CFR
    command = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-ss', str(start_time),  # Start time in seconds
        '-to', str(end_time),    # End time in seconds
        '-i', input_path,
        '-c:v', 'libx264',       # H.264 encoder
        '-r', str(target_fps),   # Target constant framerate
        '-vsync', 'cfr',         # Force CFR
        '-crf', '18',            # Quality (lower = better)
        output_path
    ]
    subprocess.run(command, check=True)

input_video = 'input_vfr.mp4'
output_video = 'output_cfr.mp4'

# Detect start/end times of non-uniform content
start, end = detect_uniform_sections(input_video)
print(f"Trimming from {start:.2f}s to {end:.2f}s")

# Trim and export as CFR
trim_and_convert_to_cfr(input_video, output_video, start, end)