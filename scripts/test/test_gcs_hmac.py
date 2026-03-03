#!/usr/bin/env python3
"""Test GCS HMAC upload - multiple methods."""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Load credentials
bucket = os.getenv("GCP_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME") or "ai_support_bucket_1"
access_key = os.getenv("S3_ACCESS_KEY")
secret_key = os.getenv("S3_SECRET_KEY")
endpoint = os.getenv("S3_ENDPOINT", "https://storage.googleapis.com")

print(f"Bucket: {bucket}")
print(f"Endpoint: {endpoint}")
print(f"Access Key: {access_key[:12]}..." if access_key else "MISSING")
print(f"Secret Key: {'*' * 8}" if secret_key else "MISSING")

if not all([bucket, access_key, secret_key]):
    print("\nERROR: Missing credentials")
    exit(1)

# For GCS HMAC, the key format matters:
# - User account HMAC: starts with "GOOG1"
# - Service account HMAC: starts with "GOOG4" (this is correct)
print(f"\nKey type: {'Service Account HMAC' if access_key.startswith('GOOG4') else 'User Account HMAC' if access_key.startswith('GOOG1') else 'Unknown'}")

test_content = f"Test upload from SupaAgent at {datetime.now()}"
test_filename = "test_upload.txt"

# Try different configurations
configs = [
    {
        "name": "Config 1: No region, virtual addressing",
        "params": {
            "endpoint_url": endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'}
            )
        }
    },
    {
        "name": "Config 2: No region, path addressing", 
        "params": {
            "endpoint_url": endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "config": Config(
                signature_version='s3v4',
                s3={'addressing_style': 'path'}
            )
        }
    },
    {
        "name": "Config 3: us-central1 region",
        "params": {
            "endpoint_url": endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": "us-central1",
            "config": Config(signature_version='s3v4')
        }
    },
    {
        "name": "Config 4: auto region",
        "params": {
            "endpoint_url": endpoint,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": "auto",
            "config": Config(signature_version='s3v4')
        }
    },
]

for cfg in configs:
    print(f"\n--- Trying {cfg['name']} ---")
    try:
        s3 = boto3.client('s3', **cfg['params'])
        s3.put_object(Bucket=bucket, Key=test_filename, Body=test_content.encode())
        print(f"SUCCESS! Uploaded {test_filename}")
        
        # List to verify
        response = s3.list_objects_v2(Bucket=bucket, MaxKeys=5)
        if 'Contents' in response:
            print("Objects in bucket:")
            for obj in response['Contents']:
                print(f"  - {obj['Key']}")
        break  # Success, stop trying
        
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        print(f"FAILED: {error_code} - {error_msg[:80]}")
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:80]}")
