import urllib.request
import mimetypes
import uuid
import os
import json

def upload_file(url, file_path):
    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or "application/octet-stream"
    
    boundary = uuid.uuid4().hex
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    }
    
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {mime_type}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return {"error_code": error.code, "message": error.read().decode("utf-8")}

# Upload
res = upload_file("http://localhost:5000/api/parse-enquiry-file", "RFQ-LIGHT FIXTURES-KOSMO ONE 12TH FLOOR-CHENNAI.xlsx")
print("Response keys:", res.keys())
if "error" in res:
    print("Error:", res["error"])
else:
    print("Message:", res.get("message"))
    print("Extracted character count:", len(res.get("extracted_text", "")))
    print("Preview (First 300 chars):")
    print(res.get("extracted_text", "")[:300])
