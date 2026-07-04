import os
import requests
import json
import time

API_KEY = os.environ.get("GEMINI_API_KEY", "")
IMAGE_PATH = r"C:\Users\Asus\.gemini\antigravity\brain\254f0c69-e609-4f38-9d81-b2f7b80d026a\media__1783090822191.png"

print("1. Parsing Image Enquiry...")
start = time.time()
with open(IMAGE_PATH, "rb") as f:
    files = {"file": f}
    data = {"gemini_api_key": API_KEY}
    response = requests.post("http://127.0.0.1:5000/api/parse-enquiry-file", files=files, data=data)

if response.status_code != 200:
    print(f"Error parsing image: {response.text}")
    exit(1)

extracted_text = response.json().get("text", "")
print(f"Time taken to parse: {time.time() - start:.1f}s")
print(f"\n--- Extracted Text ---\n{extracted_text}\n----------------------\n")

print("2. Generating Quotation...")
start = time.time()
response = requests.post(
    "http://127.0.0.1:5000/api/generate-quotation",
    json={
        "enquiry": extracted_text,
        "gemini_api_key": API_KEY,
        "ai_engine": "gemini"
    },
    timeout=180
)

print(f"Time taken to generate: {time.time() - start:.1f}s")
print(f"Status Code: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except:
    print(response.text)
