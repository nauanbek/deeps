"""
Application-wide constants.

Centralizes magic numbers and configuration values for maintainability.
"""

# ============================================================================
# Security Constants
# ============================================================================

# JWT Token Configuration
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
SECRET_KEY_MIN_LENGTH = 32

# Password Security
BCRYPT_ROUNDS = 12  # bcrypt cost factor (2^12 iterations)
PASSWORD_MIN_LENGTH = 8
PASSWORD_RECOMMENDED_MIN_LENGTH = 12
PASSWORD_MAX_SCORE_LENGTH = 20  # Max length for scoring calculation

# Password Scoring Thresholds
PASSWORD_SCORE_WEAK_THRESHOLD = 30
PASSWORD_SCORE_MEDIUM_THRESHOLD = 50
PASSWORD_SCORE_STRONG_THRESHOLD = 70

# Password Scoring Weights
PASSWORD_SCORE_PER_CHAR = 1
PASSWORD_SCORE_UPPERCASE = 10
PASSWORD_SCORE_LOWERCASE = 10
PASSWORD_SCORE_DIGIT = 10
PASSWORD_SCORE_SPECIAL = 15
PASSWORD_SCORE_LENGTH_12_BONUS = 10
PASSWORD_SCORE_LENGTH_16_BONUS = 10
PASSWORD_SCORE_MIXED_BONUS = 15
PASSWORD_SCORE_COMMON_PENALTY = 30
PASSWORD_SCORE_CONSECUTIVE_PENALTY = 10

# ============================================================================
# Rate Limiting Constants
# ============================================================================

# Default Rate Limits (requests per window)
RATE_LIMIT_DEFAULT = 60
RATE_LIMIT_WINDOW_SECONDS = 60  # 1 minute

# Endpoint-specific Rate Limits
RATE_LIMIT_EXECUTIONS = 10  # Agent execution requests per minute
RATE_LIMIT_ANALYTICS = 30  # Analytics requests per minute
RATE_LIMIT_AUTH = 5  # Auth requests per minute (brute force prevention)

# External Tools Rate Limits
RATE_LIMIT_TOOL_EXECUTIONS = 60  # Tool executions per minute
RATE_LIMIT_OAUTH_ATTEMPTS = 10  # OAuth connection attempts per hour
RATE_LIMIT_API_REQUESTS = 100  # General API requests per minute

# Rate Limiting Time Windows (seconds)
RATE_LIMIT_HOUR_SECONDS = 3600  # 1 hour
RATE_LIMIT_MINUTE_SECONDS = 60  # 1 minute

# ============================================================================
# Database Constants
# ============================================================================

# Connection Pool Configuration
DB_POOL_SIZE = 20  # Base connection pool size
DB_MAX_OVERFLOW = 40  # Maximum overflow connections
DB_POOL_RECYCLE_SECONDS = 3600  # Recycle connections after 1 hour

# Query Limits
DB_DEFAULT_LIMIT = 100  # Default pagination limit
DB_MAX_LIMIT = 1000  # Maximum allowed pagination limit

# ============================================================================
# Cache Constants (Redis)
# ============================================================================

# Default TTL (time-to-live) values in seconds
CACHE_DEFAULT_TTL = 300  # 5 minutes
CACHE_SHORT_TTL = 60  # 1 minute
CACHE_MEDIUM_TTL = 600  # 10 minutes
CACHE_LONG_TTL = 3600  # 1 hour
CACHE_DAY_TTL = 86400  # 24 hours

# ============================================================================
# Pagination Constants
# ============================================================================

# Default limits for various endpoints
PAGINATION_AGENT_LIST = 100
PAGINATION_TOOL_LIST = 100
PAGINATION_EXECUTION_LIST = 100
PAGINATION_EXECUTION_TRACES = 1000
PAGINATION_ANALYTICS_TOP_N = 10
PAGINATION_TEMPLATE_LIST = 20
PAGINATION_EXTERNAL_TOOLS = 50

# ============================================================================
# Monitoring & Metrics Constants
# ============================================================================

# Prometheus Histogram Buckets (seconds)
METRICS_LATENCY_BUCKETS = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
METRICS_QUERY_BUCKETS = [0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]

# Alert Thresholds
ALERT_ERROR_RATE_THRESHOLD = 0.05  # 5% error rate
ALERT_HIGH_LATENCY_MS = 1000  # 1 second
ALERT_LOW_SUCCESS_RATE = 0.95  # 95% success rate

# ============================================================================
# External Tools Constants
# ============================================================================

# PostgreSQL Tool Defaults
POSTGRES_DEFAULT_TIMEOUT = 30  # seconds
POSTGRES_DEFAULT_ROW_LIMIT = 1000
POSTGRES_DEFAULT_PORT = 5432

# GitLab Tool Defaults
GITLAB_DEFAULT_TIMEOUT = 30  # seconds
GITLAB_API_VERSION = "v4"

# Elasticsearch Tool Defaults
ELASTICSEARCH_DEFAULT_TIMEOUT = 30  # seconds
ELASTICSEARCH_DEFAULT_SIZE = 100

# HTTP Client Tool Defaults
HTTP_CLIENT_DEFAULT_TIMEOUT = 30  # seconds
HTTP_CLIENT_MAX_REDIRECTS = 5

# ============================================================================
# Encryption Constants
# ============================================================================

# Fernet (AES-128 CBC + HMAC)
FERNET_KEY_LENGTH = 32  # bytes (base64-encoded = 44 chars)

# ============================================================================
# Validation Constants
# ============================================================================

# Agent Configuration
AGENT_NAME_MIN_LENGTH = 1
AGENT_NAME_MAX_LENGTH = 255
AGENT_MAX_TOKENS_MIN = 1
AGENT_MAX_TOKENS_MAX = 128000  # Claude 3.5 Sonnet max
AGENT_TEMPERATURE_MIN = 0.0
AGENT_TEMPERATURE_MAX = 2.0

# Tool Configuration
TOOL_NAME_MIN_LENGTH = 1
TOOL_NAME_MAX_LENGTH = 100
TOOL_DESCRIPTION_MAX_LENGTH = 1000

# ============================================================================
# HTTP Status Code Constants (FastAPI-compatible)
# ============================================================================
# Note: Use fastapi.status module for standard codes
# These are custom/frequently used codes

HTTP_STATUS_OK = 200
HTTP_STATUS_CREATED = 201
HTTP_STATUS_BAD_REQUEST = 400
HTTP_STATUS_UNAUTHORIZED = 401
HTTP_STATUS_FORBIDDEN = 403
HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_TOO_MANY_REQUESTS = 429
HTTP_STATUS_INTERNAL_ERROR = 500

# ============================================================================
# Timeouts & Intervals (seconds)
# ============================================================================

DEFAULT_TIMEOUT = 30
LONG_TIMEOUT = 300  # 5 minutes
SHORT_TIMEOUT = 5

# ============================================================================
# Feature Flags
# ============================================================================

# Enable/disable features (can be moved to env vars)
ENABLE_RATE_LIMITING = True
ENABLE_CACHING = True
ENABLE_METRICS = True
ENABLE_EXTERNAL_TOOLS = True
