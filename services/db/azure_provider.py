import os
import mysql.connector
from mysql.connector import pooling
from .base import BaseDBProvider

class AzureDBProvider(BaseDBProvider):
    """Azure Database MySQL provider implementation."""

    def init_pool(self):
        try:
            # Azure sometimes requires the server name appended to the username (e.g., user@server)
            return mysql.connector.pooling.MySQLConnectionPool(
                pool_name="azure_pool",
                pool_size=5,
                pool_reset_session=True,
                host=os.getenv("AZURE_DB_HOST"),
                port=int(os.getenv("AZURE_DB_PORT", 3306)),
                database=os.getenv("AZURE_DB_DATABASE"),
                user=os.getenv("AZURE_DB_USER"),
                password=os.getenv("AZURE_DB_PASSWORD"),
                ssl_ca=os.getenv("AZURE_DB_SSL_CA") # Might be needed for Azure DB connections
            )
        except Exception as e:
            print(f"Error initializing Azure DB pool: {e}")
            return None
