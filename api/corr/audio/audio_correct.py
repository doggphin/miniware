import gc
import io
import os
from typing import Dict, List, Tuple
import librosa
import numpy as np
from pydub import AudioSegment
import soundfile as sf

from corr.correction_problem import GenericProblem

"""
    - Loading as many 30-120 minute .WAV files as the server has cores is incredibly memory intensive.
    It's a little excessive, but all the gc.collect() calls are to help reduce memory usage.
"""

MIN_ALLOWED_BURST_OF_AUDIO_DURING_SILENCE_SECONDS = 1
CLIPPED_AUDIO_PADDING_SECONDS = 3
QUIET_THRESHHOLD = 30

FINAL_DBFS = -3 


def adaptive_hard_clip(y: np.ndarray, clip_factor: float = 1.66) -> bool:
    """Mutates audio passed in.
    If spikes are detected, clips all loud sounds at 99.98th percentile of audio."""
    # Compute the 90th and 99th percentile levels
    loudish = np.percentile(np.abs(y), 99)
    spike_level = np.percentile(np.abs(y), 99.98)
    print(f"Loudish level (90th percentile): {loudish}, Spike level (99th percentile): {spike_level}")

    # Only apply clipping if the spike level is significantly higher than the loudish level.
    if spike_level > loudish * clip_factor:
        print(f"Significant spikes detected. Clipping values above {spike_level}.")
        # Only modify samples that exceed the 99th percentile.
        y = np.where(np.abs(y) > spike_level, np.sign(y) * spike_level, y)
        return True
    else:
        print("No significant spikes detected. No clipping applied.")
        return False


def compute_gain(y: np.ndarray, target_dbfs: float) -> float:
    """
    Computes the gain required to boost the maximum absolute amplitude of y to the target_dbfs.
    """
    peak = np.max(np.abs(y))
    if peak <= 0:
        return 1.0  # Avoid divide by zero if audio is silent
    peak_db = 20 * np.log10(peak)
    gain = 10 ** ((target_dbfs - peak_db) / 20)
    print(f"Current peak: {peak} (dB: {peak_db:.2f}). Computed gain: {gain:.3f}")
    return gain


def get_start_and_end(y: np.ndarray, sr: int, silence_threshhold : int = 30) -> Tuple[int, int]:
    """
    Finds where a track starts and ends (with some padding).
    Returns the full range (0, len(y)) if no significant audio is detected.
    """
    print(f"Analyzing audio with silence threshold: {silence_threshhold} dB")
    intervals = librosa.effects.split(y, top_db=silence_threshhold)
    print(f"Found {len(intervals)} intervals above threshold")
    
    min_duration_samples = int(MIN_ALLOWED_BURST_OF_AUDIO_DURING_SILENCE_SECONDS * sr)
    filtered_intervals = [interval for interval in intervals if (interval[1] - interval[0]) >= min_duration_samples]
    print(f"After filtering short bursts: {len(filtered_intervals)} intervals remain")

    if filtered_intervals:
        margin_samples = int(CLIPPED_AUDIO_PADDING_SECONDS * sr)
        track_start = max(0, filtered_intervals[0][0] - margin_samples)
        track_end = min(len(y), filtered_intervals[-1][1] + margin_samples)
        print(f"Audio detected from sample {track_start} to {track_end}")
        return track_start, track_end

    print("No significant audio detected, using full range")
    return 0, len(y)  # Return full range if no intervals found

def correct_audio(from_path: str, to_dir: str, options : Dict[str, any]) -> List[str]:
    # Initialize options if None
    if options is None:
        options = {}
    
    # Get silence threshold option with default value
    silence_threshold_db = options.get("audioSilenceThreshholdDb", 30)
    
    file_name, file_extension = os.path.splitext(os.path.basename(from_path))
    to_path = os.path.join(to_dir, f"{file_name}.mp3")

    # Load the audio file in stereo (preserving channels)
    y, sr = librosa.load(from_path, sr=None, mono=False)

    # For silence trimming, create a mono mix
    if y.ndim == 2:
        y_mono = librosa.to_mono(y)
    else:
        y_mono = y
    start, end = get_start_and_end(y_mono, sr, silence_threshold_db)

    # Trim silence from the beginning and end using the mono version
    # After that, we don't need y_mono anymore, so collect it
    del y_mono
    gc.collect()

    # Apply the same trimming to the stereo audio if necessary
    if y.ndim == 2:
        y = y[:, start:end]
    else:
        y = y[start:end]

    # Process the audio channels separately if stereo
    if y.ndim == 2:
        processed_channels = []
        for channel in y:
            _ = adaptive_hard_clip(channel)    # Clip channel
            gain = compute_gain(channel, FINAL_DBFS)
            channel = np.clip(channel * gain, -1.0, 1.0)  # Process channel
            processed_channels.append(channel)
        # Recombine channels (resulting array shape: (n_channels, n_samples))
        y = np.vstack(processed_channels)
    else:
        _ = adaptive_hard_clip(y)
        gain = compute_gain(y, FINAL_DBFS)
        y = np.clip(y * gain, -1.0, 1.0)

    # Convert to 16-bit PCM and save as a temporary WAV file.
    # For stereo audio, soundfile expects shape (n_samples, n_channels)
    if y.ndim == 2:
        audio_normalized_int = (y.T * 32767).astype(np.int16)
    else:
        audio_normalized_int = (y * 32767).astype(np.int16)

    # Clean up y since we don't need it anymore
    del y
    gc.collect()

    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio_normalized_int, sr, format='WAV')
    wav_buffer.seek(0)

    # clean up audio_normalized_int since we aren't using it anymore
    del audio_normalized_int
    gc.collect()

    # Load the WAV file with pydub and export as MP3
    pydub_wav = AudioSegment.from_wav(wav_buffer)
    # Optionally specify a bitrate, e.g., bitrate="320k", if needed.
    pydub_wav.export(to_path, format="mp3")
    print(f"Processed audio saved as {to_path}.")

    del wav_buffer, pydub_wav
    gc.collect()

    return [to_path]
