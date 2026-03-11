
import requests
import sys

TASK_ID = "1156b820-9f09-47a4-a409-f2e4a359eb26"
API_URL = f"http://localhost:8000/api/workers/tasks/{TASK_ID}"



def check_task():
    print(f"Fetching task {TASK_ID}...")
    try:
        resp = requests.get(f"http://localhost:8000/workers/tasks/{TASK_ID}")
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print("Error Response:")
            print(resp.text)
        else:
            print("Success:")
            print(resp.json())
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_task()
