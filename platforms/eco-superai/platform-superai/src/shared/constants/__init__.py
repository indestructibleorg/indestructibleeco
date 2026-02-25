"""Application-wide constants."""
from __future__ import annotations


class AppConstants:
    """Global application constants."""

    # API
    API_PREFIX = "/api/v1"
    API_TITLE = "SuperAI Platform"
    API_VERSION = "1.0.0"

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1

    # Auth
    TOKEN_TYPE = "bearer"
    AUTH_HEADER = "Authorization"
    BCRYPT_ROUNDS = 12

    # Rate Limiting
    DEFAULT_RATE_LIMIT = 100  # requests per minute
    AUTH_RATE_LIMIT = 10  # login attempts per minute

    # Quantum
    MAX_QUBITS = 30
    DEFAULT_SHOTS = 1024
    MAX_SHOTS = 100000

    # AI
    MAX_EMBEDDING_BATCH = 100
    MAX_PROMPT_LENGTH = 10000
    DEFAULT_TOP_K = 10

    # Scientific
    MAX_MATRIX_SIZE = 1000
    MAX_DATASET_ROWS = 100000

    # Cache TTL (seconds)
    CACHE_TTL_SHORT = 60
    CACHE_TTL_MEDIUM = 300
    CACHE_TTL_LONG = 3600
    CACHE_TTL_DAY = 86400

    # Health
    HEALTH_CHECK_TIMEOUT = 5  # seconds


class HTTPStatus:
    """Common HTTP status codes."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503


__all__ = ["AppConstants", "HTTPStatus"]