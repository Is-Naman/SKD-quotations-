import os
import app
import sys

API_KEY = os.environ.get("GEMINI_API_KEY", "")
IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity\brain\254f0c69-e609-4f38-9d81-b2f7b80d026a\media__1783090822191.png"

try:
    text = app.run_gemini_vision_ocr(IMAGE_PATH, API_KEY)
    print(f"Extracted Text length: {len(text)}")
    if not text:
        print("Text was empty!")
except Exception as e:
    print(f"Exception: {e}")
