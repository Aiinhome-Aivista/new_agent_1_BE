from abc import ABC, abstractmethod

class BaseStorageProvider(ABC):
    """Abstract base class for all storage providers."""

    @abstractmethod
    def save_file(self, file_obj, bucket_name, object_key):
        """
        Save a file to the storage provider.
        
        Args:
            file_obj: The file object or stream to save.
            bucket_name: The target container/bucket name (for local it could be ignored or prepended).
            object_key: The target path/filename inside the container.
            
        Returns:
            tuple: (bool success, str message)
        """
        pass
