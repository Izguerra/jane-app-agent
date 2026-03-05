#!/usr/bin/env python3
"""Test script to verify GCS bucket upload works."""
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os
from datetime import datetime

# Load .env file explicitly
load_dotenv()

# Load credentials from env
bucket = os.getenv("GCP_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME")
access_key = os.getenv("S3_ACCESS_KEY")
secret_key = os.getenv("S3_SECRET_KEY")
endpoint = os.getenv("S3_ENDPOINT", "https://storage.googleapis.com")
region = os.getenv("S3_REGION", "us-east1")

print(f"Bucket: {bucket}")
print(f"Endpoint: {endpoint}")
print(f"Region: {region}")
print(f"Access Key: {access_key[:10]}..." if access_key else "Access Key: MISSING")
print(f"Secret Key: {'*' * 8}" if secret_key else "Secret Key: MISSING")

if not all([bucket, access_key, secret_key]):
    print("ERROR: Missing required credentials")
    exit(1)

# Create S3 client with GCS interoperability settings
try:
    # GCS requires path-style addressing and specific signature version
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region if region else 'auto',
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}  # Required for GCS
        )
    )
    
    # Try to upload a test file
    test_content = f"Test upload from SupaAgent at {datetime.now()}".encode()
    test_filename = "test_upload.txt"
    
    print(f"\nUploading test file: {test_filename}")
    s3_client.put_object(
        Bucket=bucket,
        Key=test_filename,
        Body=test_content,
        ContentType='text/plain'
    )
    print(f"SUCCESS: Uploaded {test_filename} to {bucket}")
    
    # List objects to verify
    print("\nListing objects in bucket:")
    response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=10)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"  - {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("  No objects found")
        
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
