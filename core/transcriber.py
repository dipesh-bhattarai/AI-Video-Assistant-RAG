import whisper
import os

WHISPER_MODEL = os.getenv("WHISPER_MODEL","small")

_model = None
def load_model():
    global _model

    if _model is None:
        print(f"Loading model ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whiaper model loaded successfully")

    return _model
