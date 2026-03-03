import requests
import io

url = "http://127.0.0.1:8000/workspaces/tm_ead0lel3nkag/knowledge-base/upload"

# Create a dummy text file (easier than PDF for first test)
files = {'file': ('test_doc.txt', io.BytesIO(b"This is a test document content for indexing."), 'text/plain')}

print(f"Uploading to {url}...")
try:
    response = requests.post(url, files=files)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
