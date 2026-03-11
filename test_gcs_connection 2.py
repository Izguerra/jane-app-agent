import boto3
import os
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gcs_connection():
    bucket_name = os.getenv("S3_BUCKET_NAME") or os.getenv("GCP_BUCKET_NAME")
    s3_endpoint = os.getenv("S3_ENDPOINT", "https://storage.googleapis.com")
    s3_access_key = os.getenv("S3_ACCESS_KEY")
    s3_secret_key = os.getenv("S3_SECRET_KEY")
    s3_region = os.getenv("S3_REGION", "us-east-1")

    print(f"Testing GCS Connection:")
    print(f"Bucket: {bucket_name}")
    print(f"Endpoint: {s3_endpoint}")
    print(f"Access Key: {'*' * 4 if s3_access_key else 'Missing'}")
    print(f"Secret Key: {'*' * 4 if s3_secret_key else 'Missing'}")

    if not all([bucket_name, s3_access_key, s3_secret_key]):
        print("ERROR: Missing required credentials.")
        return

    try:
        # Initialize boto3 client with path-style addressing
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key,
            region_name=s3_region,
            config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
        )

        # 1. List Buckets (Test connectivity)
        print("\n1. Listing Buckets...")
        response = s3_client.list_buckets()
        print("   Success! Buckets found:")
        for bucket in response['Buckets']:
            print(f"   - {bucket['Name']}")

        # 2. Upload Dummy File
        print("\n2. Uploading Test File...")
        test_filename = "test_connection_file.txt"
        s3_client.put_object(Bucket=bucket_name, Key=test_filename, Body=b"Hello GCS from JaneAppAgent!")
        print(f"   Success! Uploaded {test_filename}")

        # 3. Generate Presigned URL
        print("\n3. Generating Presigned URL...")
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': test_filename},
            ExpiresIn=3600
        )
        print(f"   URL: {url}")
        
        # 4. Cleanup
        # print("\n4. Cleaning up...")
        # s3_client.delete_object(Bucket=bucket_name, Key=test_filename)
        # print("   Success! Deleted test file.")

    except ClientError as e:
        print(f"\nERROR: AWS/Boto3 Client Error: {e}")
    except Exception as e:
        print(f"\nERROR: Unexpected Error: {e}")

if __name__ == "__main__":
    test_gcs_connection()
