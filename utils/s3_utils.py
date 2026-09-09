import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load env variables explicitly
load_dotenv()

def get_s3_client():
    """Initializes and returns an S3 client using environment variables."""
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    if not access_key or not secret_key:
        print("Warning: AWS S3 credentials are not set in the environment.")
        return None
        
    return boto3.client(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )

def upload_to_s3(file_obj, bucket_name, s3_key):
    """
    Uploads a file object to the configured storage provider.
    Maintains the 'upload_to_s3' name for backward compatibility.
    """
    from services.storage import get_storage_provider
    provider = get_storage_provider()
    return provider.save_file(file_obj, bucket_name, s3_key)
