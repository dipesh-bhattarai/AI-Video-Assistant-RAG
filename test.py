from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
import os

print("KEY LOADED:", os.getenv("SARVAM_API_KEY"))  # should print your key

print("CWD:", os.getcwd())

source = "https://youtu.be/KGynZJ8ai6M?si=HfPaaIeXk9BiXu0P"
language = "hinglish"  # change to "hinglish" to test Sarvam

chunks = process_input (source)
transcript = transcribe_all(chunks, language=language)

print("\n === TRANSCRIPT === \n")
print(transcript)


