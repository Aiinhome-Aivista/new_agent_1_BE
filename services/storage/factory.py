import os
from .local_storage import LocalStorageProvider
from .aws_storage import AwsStorageProvider
from .azure_storage import AzureStorageProvider

class StorageFactory:
    """Factory to get the configured storage provider."""
    
    _provider = None

    @classmethod
    def get_provider(cls):
        if cls._provider is not None:
            return cls._provider

        cloud_provider = os.getenv("CLOUD_PROVIDER", "DEFAULT").upper()
        
        if cloud_provider == "AWS":
            cls._provider = AwsStorageProvider()
        elif cloud_provider == "AZURE":
            cls._provider = AzureStorageProvider()
        else:
            cls._provider = LocalStorageProvider()
            
        return cls._provider
