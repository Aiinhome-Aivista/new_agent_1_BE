from abc import ABC, abstractmethod

class BaseDBProvider(ABC):
    """Abstract base class for all database providers."""

    @abstractmethod
    def init_pool(self):
        """
        Initialize and return a database connection pool.
        
        Returns:
            The connection pool object depending on the implementation (e.g., mysql.connector.pooling.MySQLConnectionPool).
        """
        pass
