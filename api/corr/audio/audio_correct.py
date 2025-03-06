import io
from typing import List, Tuple
import librosa
import numpy as np
from pydub import AudioSegment
import soundfile as sf

from corr.correction_problem import GenericProblem

MIN_ALLOWED_BURST_OF_AUDIO_DURING_SILENCE_SECONDS = 1
CLIPPED_AUDIO_PADDING_SECONDS = 3
QUIET_THRESHHOLD = 30

FINAL_DBFS = -3 


def adaptive_hard_clip(y: np.ndarray, clip_factor: float = 1.66) -> Tuple[np.ndarray, bool]:
    """If spikes are detected, clips all loud sounds at 99.98th percentile of audio."""
    # Compute the 90th and 99th percentile levels
    loudish = np.percentile(np.abs(y), 99)
    spike_level = np.percentile(np.abs(y), 99.98)
    print(f"Loudish level (90th percentile): {loudish}, Spike level (99th percentile): {spike_level}")

    # Only apply clipping if the spike level is significantly higher than the loudish level.
    if spike_level > loudish * clip_factor:
        print(f"Significant spikes detected. Clipping values above {spike_level}.")
        # Only modify samples that exceed the 99th percentile.
        y_clipped = np.where(np.abs(y) > spike_level, np.sign(y) * spike_level, y)
        return y_clipped, True
    else:
        print("No significant spikes detected. No clipping applied.")
        return y, False


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


def get_start_and_end(y: np.ndarray, sr: int) -> Tuple[int, int]:
    """
    Finds where a track starts and ends (with some padding). Returns None if the audio is blank.
    """
    intervals = librosa.effects.split(y, top_db=30)
    min_duration_samples = int(MIN_ALLOWED_BURST_OF_AUDIO_DURING_SILENCE_SECONDS * sr)
    filtered_intervals = [interval for interval in intervals if (interval[1] - interval[0]) >= min_duration_samples]

    if filtered_intervals:
        margin_samples = int(CLIPPED_AUDIO_PADDING_SECONDS * sr)
        track_start = max(0, filtered_intervals[0][0] - margin_samples)
        track_end = min(len(y), filtered_intervals[-1][1] + margin_samples)
        return track_start, track_end

    return None

def audio_correct(from_path: str, to_dir: str, args: dict[str, any]) -> List[str]:
    file_name = from_path.split("/")[-1]
    file_name, file_extension = file_name.split(".")

    # Load the audio file in stereo (preserving channels)
    y, sr = librosa.load(from_path, sr=None, mono=False)

    # For silence trimming, create a mono mix
    if y.ndim == 2:
        y_mono = librosa.to_mono(y)
    else:
        y_mono = y

    # Trim silence from the beginning and end using the mono version
    start_and_end = get_start_and_end(y_mono, sr)
    if start_and_end is None:
        raise GenericProblem("Blank audio file")
    start, end = start_and_end

    # Apply the same trimming to the stereo audio if necessary
    if y.ndim == 2:
        y = y[:, start:end]
    else:
        y = y[start:end]

    # Process the audio channels separately if stereo
    if y.ndim == 2:
        processed_channels = []
        for channel in y:
            channel_clipped, _ = adaptive_hard_clip(channel)
            gain = compute_gain(channel_clipped, FINAL_DBFS)
            processed_channel = np.clip(channel_clipped * gain, -1.0, 1.0)
            processed_channels.append(processed_channel)
        # Recombine channels (resulting array shape: (n_channels, n_samples))
        y_processed = np.vstack(processed_channels)
    else:
        y_clipped, _ = adaptive_hard_clip(y)
        gain = compute_gain(y_clipped, FINAL_DBFS)
        y_processed = np.clip(y_clipped * gain, -1.0, 1.0)

    # Convert to 16-bit PCM and save as a temporary WAV file.
    # For stereo audio, soundfile expects shape (n_samples, n_channels)
    if y_processed.ndim == 2:
        audio_normalized_int = (y_processed.T * 32767).astype(np.int16)
    else:
        audio_normalized_int = (y_processed * 32767).astype(np.int16)

    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio_normalized_int, sr, format='WAV')
    wav_buffer.seek(0)

    # Load the WAV file with pydub and export as MP3
    pydub_wav = AudioSegment.from_wav(wav_buffer)
    to_path_mp3 = f"{to_dir}/{file_name}.mp3"
    # Optionally specify a bitrate, e.g., bitrate="320k", if needed.
    pydub_wav.export(to_path_mp3, format="mp3")
    print(f"Processed audio saved as {to_path_mp3}.")

    return [to_path_mp3]
