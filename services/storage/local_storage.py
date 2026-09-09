import os
from .base import BaseStorageProvider

class LocalStorageProvider(BaseStorageProvider):
    """Local storage provider implementation."""

    def __init__(self):
        self.upload_path = os.getenv("UPLOAD_PATH", "data/uploads")

    def save_file(self, file_obj, bucket_name, object_key):
        try:
            # For local storage, bucket_name is treated as part of the directory structure if needed,
            # or ignored. We'll include it in the path for separation.
            full_path = os.path.join(self.upload_path, bucket_name, object_key)
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Save the file
            if hasattr(file_obj, 'read'):
                with open(full_path, 'wb') as f:
                    f.write(file_obj.read())
            elif isinstance(file_obj, bytes):
                with open(full_path, 'wb') as f:
                    f.write(file_obj)
            else:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(str(file_obj))
                    
            return True, f"Successfully uploaded to local storage: {full_path}"
        except Exception as e:
            return False, f"Failed to save to local storage: {str(e)}"
