import os
from .base import BaseStorageProvider

class AzureStorageProvider(BaseStorageProvider):
    """Azure Blob Storage provider implementation."""

    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not self.connection_string:
            print("Warning: AZURE_STORAGE_CONNECTION_STRING is not set.")
            self.blob_service_client = None
        else:
            try:
                from azure.storage.blob import BlobServiceClient
                self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            except ImportError:
                print("Warning: azure-storage-blob package is not installed.")
                self.blob_service_client = None

    def save_file(self, file_obj, bucket_name, object_key):
        # In Azure, bucket_name maps to container_name
        container_name = bucket_name
        if not self.blob_service_client:
            return False, "Azure Blob client could not be initialized (Missing credentials or package)."
            
        try:
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=object_key)
            if hasattr(file_obj, 'read'):
                blob_client.upload_blob(file_obj, overwrite=True)
            else:
                blob_client.upload_blob(file_obj, overwrite=True)
            return True, f"Successfully uploaded to Azure Blob: {container_name}/{object_key}"
        except Exception as e:
            return False, str(e)
