import os
import sys

from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY", "")

client = genai.Client(api_key=API_KEY)

print("Listing files...")
try:
    for f in client.files.list():
        print(f.name, f.display_name)
except Exception as e:
    print(f"Error listing files: {e}")

print("Testing upload...")
try:
    file = client.files.upload(file="uploads/Legrand (2026).pdf", config={'display_name': 'Legrand (2026).pdf'})
    print(f"Uploaded successfully: {file.name}")
except Exception as e:
    print(f"Error uploading: {e}")
