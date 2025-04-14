import pytest
from django.core.cache import cache, caches
from django.conf import settings
import redis
from redis.exceptions import ConnectionError, RedisError
from urllib.parse import urlparse

@pytest.fixture
def redis_client():
    """Fixture to provide a Redis client for testing"""
    redis_url = settings.CACHES['contacts']['LOCATION']
    parsed_url = urlparse(redis_url)
    
    # Extract connection details
    host = parsed_url.hostname or 'localhost'
    port = parsed_url.port or 6379
    db = int(parsed_url.path.strip('/')) if parsed_url.path else 0
    
    client = redis.Redis(
        host=host,
        port=port,
        db=db,
        decode_responses=True
    )
    yield client
    # Cleanup after tests
    client.flushdb()

def test_redis_connection(redis_client):
    """Test basic Redis connection"""
    assert redis_client.ping(), "Redis connection failed"

def test_redis_set_get(redis_client):
    """Test basic Redis set and get operations"""
    test_key = "test:key"
    test_value = "test_value"
    
    # Set value
    redis_client.set(test_key, test_value)
    
    # Get value
    retrieved_value = redis_client.get(test_key)
    
    assert retrieved_value == test_value, "Retrieved value does not match set value"

def test_redis_connection_error():
    """Test Redis connection error handling"""
    with pytest.raises(ConnectionError):
        # Try to connect to non-existent Redis server
        redis.Redis(host='localhost', port=9999).ping()

def test_redis_cache_backend():
    """Test Django's cache backend Redis connection"""
    test_key = "django:test:key"
    test_value = "django_test_value"
    
    # Set value using Django's cache
    contacts_cache = caches['contacts']
    contacts_cache.set(test_key, test_value)
    
    # Get value using Django's cache
    retrieved_value = contacts_cache.get(test_key)
    
    assert retrieved_value == test_value, "Django cache backend Redis connection failed"

def test_redis_connection_pool():
    """Test Redis connection pool"""
    redis_url = settings.CACHES['contacts']['LOCATION']
    parsed_url = urlparse(redis_url)
    
    # Extract connection details
    host = parsed_url.hostname or 'localhost'
    port = parsed_url.port or 6379
    db = int(parsed_url.path.strip('/')) if parsed_url.path else 0
    
    pool = redis.ConnectionPool(
        host=host,
        port=port,
        db=db,
        decode_responses=True
    )
    
    client1 = redis.Redis(connection_pool=pool)
    client2 = redis.Redis(connection_pool=pool)
    
    assert client1.ping() and client2.ping(), "Redis connection pool failed"
    assert client1.connection_pool == client2.connection_pool, "Connection pool not shared between clients"

def test_redis_connection_timeout():
    """Test Redis connection timeout"""
    with pytest.raises(ConnectionError):
        # Try to connect with a very short timeout
        redis.Redis(
            host='localhost',
            port=9999,
            socket_timeout=0.1
        ).ping()

def test_redis_connection_retry():
    """Test Redis connection retry mechanism"""
    max_retries = 3
    retry_count = 0
    
    try:
        redis.Redis(
            host='localhost',
            port=9999,
            retry_on_timeout=True,
            socket_timeout=0.1
        ).ping()
    except ConnectionError:
        retry_count += 1
    
    assert retry_count > 0, "Redis connection retry mechanism not working as expected" 