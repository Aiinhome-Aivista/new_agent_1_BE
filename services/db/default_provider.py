import os
import mysql.connector
from mysql.connector import pooling
from .base import BaseDBProvider

class DefaultDBProvider(BaseDBProvider):
    """Local MySQL database provider implementation."""

    def init_pool(self):
        try:
            return mysql.connector.pooling.MySQLConnectionPool(
                pool_name="local_pool",
                pool_size=5,
                pool_reset_session=True,
                host=os.getenv("MYSQL_HOST", "localhost"),
                port=int(os.getenv("MYSQL_PORT", 3306)),
                database=os.getenv("MYSQL_NAME") or os.getenv("MYSQL_DATABASE", "test_db"),
                user=os.getenv("MYSQL_USER", "root"),
                password=os.getenv("MYSQL_PASSWORD", "")
            )
        except Exception as e:
            print(f"Error initializing local DB pool: {e}")
            return None
