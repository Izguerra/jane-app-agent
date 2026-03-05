from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import boto3
import os
import logging
from botocore.exceptions import ClientError

# Configure logger
logger = logging.getLogger("recordings")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/api/recordings", tags=["recordings"])

@router.get("/{filename}")
async def get_recording(filename: str):
    """
    Generates a presigned URL for the requested recording file and redirects the user to it.
    This avoids proxying the file content through the server.
    """
    logger.info(f"Received request for recording: {filename}")
    
    from backend.services.storage_service import get_storage_service
    storage = get_storage_service()
    
    if not storage.s3_client:
        logger.error("Storage configuration missing")
        raise HTTPException(status_code=500, detail="Storage configuration missing")

    presigned_url = storage.generate_presigned_url(filename)
    
    if not presigned_url:
        raise HTTPException(status_code=500, detail="Failed to generate recording link")
    
    logger.info(f"Generated presigned URL for {filename}: {presigned_url}")
    
    # Redirect to the S3 URL
    return RedirectResponse(url=presigned_url)
