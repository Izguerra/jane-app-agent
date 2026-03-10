#!/usr/bin/env python3
"""Test DigitalOcean Spaces upload."""
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

# Get the newest values (they're at the end of the file)
bucket = os.getenv("S3_BUCKET_NAME")
access_key = os.getenv("S3_ACCESS_KEY")
secret_key = os.getenv("S3_SECRET_KEY")
endpoint = os.getenv("S3_ENDPOINT")
region = os.getenv("S3_REGION")

print(f"Bucket: {bucket}")
print(f"Endpoint: {endpoint}")
print(f"Region: {region}")
print(f"Access Key: {access_key[:8]}..." if access_key else "MISSING")

# For DigitalOcean Spaces, endpoint should be region-based, not bucket-based
# Correct format: https://tor1.digitaloceanspaces.com
if endpoint and 'digitaloceanspaces.com' in endpoint and bucket and bucket in endpoint:
    # Fix endpoint by removing bucket name
    endpoint = endpoint.replace(f"{bucket}.", "")
    print(f"Fixed endpoint: {endpoint}")

try:
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}  # Required for non-AWS S3
        )
    )
    
    # Try to upload
    test_content = f"Test upload from SupaAgent at {datetime.now()}"
    test_filename = "test_upload.txt"
    
    print(f"\nUploading {test_filename} to {bucket}...")
    s3.put_object(
        Bucket=bucket,
        Key=test_filename,
        Body=test_content.encode(),
        ContentType='text/plain'
    )
    print(f"SUCCESS! Uploaded {test_filename}")
    
    # List objects
    print("\nObjects in bucket:")
    response = s3.list_objects_v2(Bucket=bucket, MaxKeys=5)
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"  - {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("  Bucket is empty or no objects found")
        
except Exception as e:
    import traceback
    print(f"\nERROR: {type(e).__name__}: {e}")
    traceback.print_exc()
