"""
Rate limiting settings for the RBAC API.
"""

# Enable/disable rate limiting
RATE_LIMIT_ENABLED = True

# Number of requests allowed per window
RATE_LIMIT_REQUESTS = 100

# Time window in seconds
RATE_LIMIT_WINDOW = 60

# Cache key prefix
RATE_LIMIT_CACHE_PREFIX = 'rate_limit:'

# Rate limit headers
RATE_LIMIT_HEADERS = {
    'X-RateLimit-Limit': 'X-RateLimit-Limit',
    'X-RateLimit-Remaining': 'X-RateLimit-Remaining',
    'X-RateLimit-Reset': 'X-RateLimit-Reset',
    'Retry-After': 'Retry-After'
} 