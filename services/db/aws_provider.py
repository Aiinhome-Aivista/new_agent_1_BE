import os
import mysql.connector
from mysql.connector import pooling
from .base import BaseDBProvider

class AwsDBProvider(BaseDBProvider):
    """AWS RDS MySQL database provider implementation."""

    def init_pool(self):
        try:
            return mysql.connector.pooling.MySQLConnectionPool(
                pool_name="aws_pool",
                pool_size=5,
                pool_reset_session=True,
                host=os.getenv("AWS_RDS_HOST"),
                port=int(os.getenv("AWS_RDS_PORT", 3306)),
                database=os.getenv("AWS_RDS_DATABASE"),
                user=os.getenv("AWS_RDS_USER"),
                password=os.getenv("AWS_RDS_PASSWORD")
            )
        except Exception as e:
            print(f"Error initializing AWS DB pool: {e}")
            return None
