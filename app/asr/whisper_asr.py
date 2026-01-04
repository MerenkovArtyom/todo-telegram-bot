from pathlib import Path
import whisper
import subprocess

AUDIO_DIR = Path("data/audio")
MODEL_NAME = "tiny"  # оптимально для слабого ПК

_model = None


def load_model():
    global _model
    if _model is None:
        _model = whisper.load_model(MODEL_NAME)
    return _model


def ogg_to_wav(ogg_path: Path) -> Path:
    wav_path = ogg_path.with_suffix(".wav")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i", str(ogg_path),
            "-ar", "16000",
            "-ac", "1",
            str(wav_path),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    return wav_path


def transcribe(ogg_path: Path) -> str:
    wav_path = ogg_to_wav(ogg_path)
    model = load_model()

    result = model.transcribe(
        str(wav_path),
        language="ru",
        fp16=False
    )

    return result["text"].strip()
