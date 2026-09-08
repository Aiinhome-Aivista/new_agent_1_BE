from .factory import StorageFactory

def get_storage_provider():
    return StorageFactory.get_provider()
