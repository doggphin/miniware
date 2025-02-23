import io
from typing import List, Tuple
import librosa
import numpy as np
from pydub import AudioSegment
import soundfile as sf

from corr.correction_problem import CorrectionProblem

MIN_ALLOWED_BURST_OF_AUDIO_DURING_SILENCE_SECONDS = 1
CLIPPED_AUDIO_PADDING_SECONDS = 3


import numpy as np


def clip_and_normalize_audio(y : np.ndarray, sr : int) -> Tuple[np.ndarray, int]:
    # Detect non-silent intervals
    intervals = librosa.effects.split(y, top_db=40)

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

        # Trim the audio
        y_trimmed = y[track_start:track_end]
        return [y_trimmed, sr]
    else:
        print("No non-silent interval longer than the threshold was found.")
        return None


def audio_correct(from_path: str, to_dir: str, args: dict[str, any]) -> List[str]:
    file_name = from_path.split("/")[-1]
    file_name, file_extension = file_name.split(".")

    if "R2R" in file_name.split("_"):
        # Run following code on both the L and R track of the audio file at from_path
        pass
    
    to_path = f"{to_dir}/{file_name}"

    # Load the audio file
    y, sr = librosa.load(from_path, sr=None)

    # Clip silence from ends of audio
    clipped_and_normalized = clip_and_normalize_audio(y, sr)
    if clipped_and_normalized == None:
        raise CorrectionProblem("Blank audio file")

    y, sr = clip_and_normalize_audio(y, sr)

    # Normalize audio
    y = librosa.util.normalize(y)

    audio_normalized_int = (y * 32767).astype(np.int16)

    # Save the trimmed audio as a temporary WAV file
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