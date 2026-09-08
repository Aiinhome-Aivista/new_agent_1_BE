from .factory import DBFactory

def get_db_provider():
    return DBFactory.get_provider()
