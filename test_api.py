import os
import requests
import json
import time

API_KEY = os.environ.get("GEMINI_API_KEY", "")
IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity\brain\254f0c69-e609-4f38-9d81-b2f7b80d026a\media__1783090822191.png"

print("1. Parsing Image Enquiry...")
with open(IMAGE_PATH, "rb") as f:
    files = {"file": f}
    data = {"gemini_api_key": API_KEY}
    response = requests.post("http://127.0.0.1:5000/api/parse-enquiry-file", files=files, data=data)

print(response.status_code)
print(response.text)
