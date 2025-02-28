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


import numpy as np


def get_peak_amplitude(y : np.ndarray) -> Tuple[float, bool]:
    """
    Returns the peak amplitude, and whether the audio should be hard clipped at all.
    """
    loudish_amplitude = np.percentile(np.abs(y), 90)
    spikes_amplitude = np.percentile(np.abs(y), 99)
    print(f"loudish at {loudish_amplitude}, spikes at {spikes_amplitude}")
    has_loud_peaks = spikes_amplitude > loudish_amplitude * 3

    peak = spikes_amplitude if has_loud_peaks else np.max(np.abs(y))
    return [peak, has_loud_peaks]


def hard_limit(y : np.ndarray, threshhold : float) -> np.ndarray:
    return np.clip(y, -threshhold, threshhold)
    # y[peaks] = np.sign(y[peaks]) * (threshhold + (np.abs(y[peaks])) - threshhold) * ratio


def get_start_and_end(y : np.ndarray, sr : int) -> Tuple[int, int]:
    """
    Finds where a track starts and ends, plus some padding. Returns None if the audio is blank.
    """
    # Detect non-silent intervals
    intervals = librosa.effects.split(y, top_db=30)

    # Filter out all the intervals shorter than the minimum duration
    min_duration_samples = int(MIN_ALLOWED_BURST_OF_AUDIO_DURING_SILENCE_SECONDS * sr)
    filtered_intervals = [interval for interval in intervals if (interval[1] - interval[0]) >= min_duration_samples]

    if filtered_intervals:
        margin_samples = int(CLIPPED_AUDIO_PADDING_SECONDS * sr)

        # Start of the first long non-silent interval
        track_start = filtered_intervals[0][0]
        track_start = max(0, track_start - margin_samples)

        # End of the last non-silent interval
        track_end = filtered_intervals[-1][1]
        track_end = min(len(y), filtered_intervals[-1][1] + margin_samples)

        return [track_start, track_end]
    
    return None


def audio_correct(from_path: str, to_dir: str, args: dict[str, any]) -> List[str]:
    file_name = from_path.split("/")[-1]
    file_name, file_extension = file_name.split(".")

    #if "R2R" in file_name.split("_"):
    #    y_stereo, sr = librosa.load(from_path, sr = None, mono = False)
    #    # Run following code on both the L and R track of the audio file at from_path
    #    pass

    # Load the audio file
    y, sr = librosa.load(from_path, sr=None)

    # Clip silence from ends of audio
    start_and_end = get_start_and_end(y, sr)
    if start_and_end == None:
        raise GenericProblem("Blank audio file") 
    y = y[start_and_end[0]:start_and_end[1]]

    # Lower audio at peaks
    peak_amplitude, should_hard_limit = get_peak_amplitude(y)

    peak_db = 20 * np.log10(peak_amplitude)
    gain = 10 ** ((FINAL_DBFS - peak_db) / 20)
    y = y * gain

    if(should_hard_limit):
        print(f"Hard limited at {peak_db}!")
        y = hard_limit(y, peak_amplitude)
    else:
        print("Did not hard limit!")

    # Save the trimmed audio as a temporary WAV file
    audio_normalized_int = (y * 32767).astype(np.int16)
    wav_buffer = io.BytesIO()
    sf.write(wav_buffer, audio_normalized_int, sr, format='WAV')
    wav_buffer.seek(0)

    # Load the WAV file with pydub
    pydub_wav = AudioSegment.from_wav(wav_buffer)

    # Export as MP3
    # output_mp3 = f"output.mp3"
    to_path_mp3 = f"{to_dir}/{file_name}.mp3"
    pydub_wav.export(to_path_mp3, format="mp3")
    print(f"Trimmed audio saved as {to_path_mp3}.")

    return [to_path_mp3]