import os
import requests
import json
import time

API_KEY = os.environ.get("GEMINI_API_KEY", "")

enquiry_text = """
1 VACCUM CIRCUIT BREAKER Supply, Installation, Testing and commissioning of Floor Mounted, Motorised, Drawout Type, Horizontal Isolation, Horizontal Drawout, 11 KV 630 A, 26.3 KA Vacuum Circuit Breaker with fully equipped panel Nos 2
Supply & laying of 3.5cx185 sqmm Al ar XLPE HT Cable Mtrs 100
"""

print("Sending request to local backend...")
start = time.time()
try:
    response = requests.post(
        "http://127.0.0.1:5000/api/generate-quotation",
        json={
            "enquiry": enquiry_text,
            "gemini_api_key": API_KEY,
            "ai_engine": "gemini"
        },
        timeout=180
    )
    print(f"Time taken: {time.time() - start:.1f}s")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
