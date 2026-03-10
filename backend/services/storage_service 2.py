
import boto3
import os
import logging
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Optional
from pathlib import Path
import shutil

logger = logging.getLogger("storage_service")

class StorageService:
    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.endpoint_url = os.getenv("S3_ENDPOINT")
        self.access_key = os.getenv("S3_ACCESS_KEY")
        self.secret_key = os.getenv("S3_SECRET_KEY")
        self.region = os.getenv("S3_REGION", "us-east-1")
        
        # Local storage path (matches main.py mount)
        self.local_upload_dir = Path("backend/data/uploads")
        self.local_upload_dir.mkdir(parents=True, exist_ok=True)

        if not all([self.bucket_name, self.endpoint_url, self.access_key, self.secret_key]):
            logger.warning("Storage configuration missing. S3 features disabled, using local storage.")
            self.s3_client = None
        else:
            try:
                self.s3_client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region,
                    config=Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
                )
                logger.info("StorageService initialized successfully (S3 + Local).")
            except Exception as e:
                logger.error(f"Failed to initialize StorageService: {e}")
                self.s3_client = None

    def upload_file(self, file_obj, filename: str, content_type: str = None) -> Optional[str]:
        """
        Uploads a file-like object to local storage and optionally S3.
        Returns the filename if successful (for local access), None otherwise.
        """
        success = False
        
        # 1. Save locally (Primary for /api/uploads access)
        try:
            local_path = self.local_upload_dir / filename
            with open(local_path, "wb") as f:
                # If file_obj is at start, read it. If not, seek 0?
                # The caller (router) already did seek(0)
                shutil.copyfileobj(file_obj, f)
            
            logger.info(f"Saved {filename} locally to {local_path}")
            success = True
            
            # Reset file pointer for S3 upload
            file_obj.seek(0)
            
        except Exception as e:
            logger.error(f"Failed to save locally {filename}: {e}")
            # If local fails, we might still try S3, but the URL won't work...
            # But let's continue.

        # 2. Upload to S3 (Backup / Production)
        if self.s3_client:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            try:
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    filename,
                    ExtraArgs=extra_args
                )
                logger.info(f"Uploaded {filename} to S3 {self.bucket_name}")
                success = True # Marked success if at least one worked
            except ClientError as e:
                logger.error(f"Failed to upload {filename} to S3: {e}")
            except Exception as e:
                logger.error(f"Unexpected error uploading {filename} to S3: {e}")

        return filename if success else None

    def generate_presigned_url(self, filename: str, expiration: int = 3600, method: str = 'get_object') -> Optional[str]:
        """
        Generates a presigned URL for accessing a file from S3.
        """
        if not self.s3_client:
            return None

        try:
            url = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket_name, 'Key': filename},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {filename}: {e}")
            return None

    def download_file(self, filename: str, target_path: str) -> bool:
        """
        Downloads a file from S3 or copies from local.
        """
        # Try local first
        local_source = self.local_upload_dir / filename
        if local_source.exists():
            try:
                Path(target_path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(local_source, target_path)
                return True
            except Exception as e:
                logger.error(f"Failed to copy local file {filename}: {e}")

        # Fallback to S3
        if not self.s3_client:
            return False

        try:
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            self.s3_client.download_file(self.bucket_name, filename, target_path)
            logger.info(f"Downloaded {filename} from S3 to {target_path}")
            return True
        except ClientError as e:
            logger.error(f"Failed to download {filename} from S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {filename} from S3: {e}")
            return False

    def delete_file(self, filename: str) -> bool:
        """
        Deletes a file from local and S3.
        """
        success = False
        
        # Delete local
        try:
            local_path = self.local_upload_dir / filename
            if local_path.exists():
                os.remove(local_path)
                logger.info(f"Deleted local file {filename}")
                success = True
        except Exception as e:
            logger.error(f"Failed to delete local file {filename}: {e}")

        # Delete S3
        if self.s3_client:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
                logger.info(f"Deleted {filename} from S3")
                success = True
            except ClientError as e:
                logger.error(f"Failed to delete {filename} from S3: {e}")
        
        return success

# Global instance
_storage_service = StorageService()

def get_storage_service():
    return _storage_service
