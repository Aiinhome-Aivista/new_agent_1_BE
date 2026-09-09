import os
from .default_provider import DefaultDBProvider
from .aws_provider import AwsDBProvider
from .azure_provider import AzureDBProvider

class DBFactory:
    """Factory to get the configured database provider."""
    
    _provider = None

    @classmethod
    def get_provider(cls):
        if cls._provider is not None:
            return cls._provider

        db_provider = os.getenv("DB_PROVIDER", "DEFAULT").upper()
        
        if db_provider == "AWS":
            cls._provider = AwsDBProvider()
        elif db_provider == "AZURE":
            cls._provider = AzureDBProvider()
        else:
            cls._provider = DefaultDBProvider()
            
        return cls._provider
