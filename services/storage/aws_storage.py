import os
import boto3
from botocore.exceptions import NoCredentialsError
from .base import BaseStorageProvider

class AwsStorageProvider(BaseStorageProvider):
    """AWS S3 storage provider implementation."""

    def __init__(self):
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        
        if self.access_key and self.secret_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
        else:
            print("Warning: AWS S3 credentials are not set in the environment.")
            self.s3_client = None

    def save_file(self, file_obj, bucket_name, object_key):
        if not self.s3_client:
            return False, "S3 client could not be initialized (Missing credentials)."
            
        try:
            self.s3_client.upload_fileobj(file_obj, bucket_name, object_key)
            return True, f"Successfully uploaded to s3://{bucket_name}/{object_key}"
        except NoCredentialsError:
            return False, "Credentials not available for S3 upload."
        except Exception as e:
            return False, str(e)
