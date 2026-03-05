#!/usr/bin/env python3
"""Test GCS upload using google-cloud-storage library."""
from google.cloud import storage
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

bucket_name = os.getenv("GCP_BUCKET_NAME") or "ai_support_bucket_1"
key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

print(f"Bucket: {bucket_name}")
print(f"Key file env: {key_file}")

# Check for common key file locations if not set
if not key_file:
    possible_paths = [
        "gcs-key.json",
        "service-account.json",
        "credentials.json",
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            key_file = path
            print(f"Found key file at: {path}")
            break

try:
    if key_file and os.path.exists(key_file):
        print("Using service account key file")
        client = storage.Client.from_service_account_json(key_file)
    else:
        print("Trying default credentials (gcloud auth)")
        client = storage.Client()

    bucket = client.bucket(bucket_name)
    blob = bucket.blob("test_upload.txt")
    blob.upload_from_string(f"Test upload from SupaAgent at {datetime.now()}")
    print(f"\nSUCCESS: Uploaded test_upload.txt to {bucket_name}")
    
    # List blobs
    print("\nBlobs in bucket:")
    for b in client.list_blobs(bucket_name, max_results=5):
        print(f"  - {b.name} ({b.size} bytes)")
        
except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {e}")
    print("\nTo fix this, you need to either:")
    print("1. Download a service account JSON key from GCP Console")
    print("   (IAM -> Service Accounts -> Keys -> Add Key)")
    print("   and set GOOGLE_APPLICATION_CREDENTIALS in .env")
    print("2. OR run: gcloud auth application-default login")
