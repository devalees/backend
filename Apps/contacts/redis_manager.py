import redis
from django.conf import settings
from redis.exceptions import ConnectionError, RedisError
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RedisConnectionManager:
    """
    Redis connection manager for the contacts app.
    Implements connection pooling and error handling.
    """
    
    _instance = None
    _pool = None
    _client = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        if cls._instance is None:
            cls._instance = super(RedisConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Redis connection pool if not already initialized"""
        if self._pool is None:
            try:
                # Parse Redis connection details from Django settings
                redis_url = settings.CACHES['contacts']['LOCATION']
                parsed_url = urlparse(redis_url)
                
                # Extract connection details
                host = parsed_url.hostname or 'localhost'
                port = parsed_url.port or 6379
                db = int(parsed_url.path.strip('/')) if parsed_url.path else 0
                
                # Create connection pool
                self._pool = redis.ConnectionPool(
                    host=host,
                    port=port,
                    db=db,
                    decode_responses=True,
                    max_connections=50,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                
                # Create Redis client
                self._client = redis.Redis(connection_pool=self._pool)
                
                # Test connection
                self._client.ping()
                logger.info("Redis connection established successfully")
                
            except (ConnectionError, RedisError) as e:
                logger.error(f"Failed to establish Redis connection: {str(e)}")
                raise
    
    @property
    def client(self):
        """Get Redis client instance"""
        if self._client is None:
            self.__init__()
        return self._client
    
    def get_connection(self):
        """Get a new Redis connection from the pool"""
        try:
            return redis.Redis(connection_pool=self._pool)
        except (ConnectionError, RedisError) as e:
            logger.error(f"Failed to get Redis connection: {str(e)}")
            raise
    
    def close(self):
        """Close Redis connection pool"""
        if self._pool:
            self._pool.disconnect()
            self._pool = None
            self._client = None
            logger.info("Redis connection pool closed") 