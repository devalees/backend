import pytest
from django.core.cache import cache
from ..redis_manager import RedisConnectionManager
from redis.exceptions import ConnectionError, RedisError
from unittest.mock import patch

@pytest.fixture
def redis_manager():
    """Fixture to provide a RedisConnectionManager instance"""
    manager = RedisConnectionManager()
    yield manager
    # Cleanup after tests
    manager.close()

def test_singleton_pattern():
    """Test that RedisConnectionManager follows singleton pattern"""
    manager1 = RedisConnectionManager()
    manager2 = RedisConnectionManager()
    assert manager1 is manager2, "RedisConnectionManager is not a singleton"

def test_redis_connection_establishment(redis_manager):
    """Test that Redis connection is established successfully"""
    assert redis_manager.client.ping(), "Redis connection not established"

def test_connection_pool_reuse(redis_manager):
    """Test that connection pool is reused"""
    client1 = redis_manager.get_connection()
    client2 = redis_manager.get_connection()
    assert client1.connection_pool is client2.connection_pool, "Connection pool not reused"

def test_redis_operations(redis_manager):
    """Test basic Redis operations through the manager"""
    test_key = "test:manager:key"
    test_value = "test_value"
    
    # Set value
    redis_manager.client.set(test_key, test_value)
    
    # Get value
    retrieved_value = redis_manager.client.get(test_key)
    
    assert retrieved_value == test_value, "Redis operations failed through manager"

@patch('redis.Redis.ping')
def test_connection_error_handling(mock_ping):
    """Test connection error handling"""
    # Mock Redis ping to raise ConnectionError
    mock_ping.side_effect = ConnectionError("Connection refused")
    
    # Create a manager with mocked connection
    with pytest.raises((ConnectionError, RedisError)):
        RedisConnectionManager._pool = None
        RedisConnectionManager._client = None
        RedisConnectionManager._instance = None
        manager = RedisConnectionManager()
        manager.client.ping()

def test_connection_pool_limits(redis_manager):
    """Test connection pool limits"""
    # Create multiple connections
    connections = [redis_manager.get_connection() for _ in range(60)]
    
    # All connections should be successful
    assert all(conn.ping() for conn in connections), "Failed to create multiple connections"

@patch('redis.Redis.ping')
def test_connection_timeout(mock_ping):
    """Test connection timeout handling"""
    # Mock Redis ping to raise ConnectionError
    mock_ping.side_effect = ConnectionError("Connection timeout")
    
    with pytest.raises((ConnectionError, RedisError)):
        # Create a manager with mocked connection
        RedisConnectionManager._pool = None
        RedisConnectionManager._client = None
        RedisConnectionManager._instance = None
        manager = RedisConnectionManager()
        manager.client.ping()

def test_connection_cleanup(redis_manager):
    """Test proper connection cleanup"""
    # Get initial connection
    initial_client = redis_manager.client
    
    # Close connections
    redis_manager.close()
    
    # Create new manager
    new_manager = RedisConnectionManager()
    
    # Should create new connection
    assert new_manager.client is not initial_client, "Connection not properly cleaned up"

def test_connection_retry():
    """Test connection retry mechanism"""
    # Create a manager with retry settings
    RedisConnectionManager._pool = None
    RedisConnectionManager._client = None
    RedisConnectionManager._instance = None
    
    manager = RedisConnectionManager()
    assert manager.client.ping(), "Connection retry failed" 