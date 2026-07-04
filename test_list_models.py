import os
import google.generativeai as genai
API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=API_KEY)
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
