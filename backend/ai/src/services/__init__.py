"""IndestructibleEco AI Services — Engine management, connection pooling, circuit breaking,
async worker, gRPC server, embedding.

URI: indestructibleeco://backend/ai/services
"""

from .circuit_breaker import CircuitBreaker, CircuitState
from .connection_pool import ConnectionPool
from .embedding import EmbeddingResult, EmbeddingService, SimilarityResult
from .engine_manager import EngineManager
from .grpc_server import (
    EmbeddingRequest as GrpcEmbeddingRequest,
    EmbeddingResponse as GrpcEmbeddingResponse,
    GenerateRequest as GrpcGenerateRequest,
    GenerateResponse as GrpcGenerateResponse,
    GrpcServer,
    GrpcServiceConfig,
    InferenceServicer,
)
from .worker import InferenceJob, InferenceWorker, JobPriority, JobStatus

__all__ = [
    "CircuitBreaker",
    "CircuitState",
    "ConnectionPool",
    "EmbeddingResult",
    "EmbeddingService",
    "EngineManager",
    "GrpcEmbeddingRequest",
    "GrpcEmbeddingResponse",
    "GrpcGenerateRequest",
    "GrpcGenerateResponse",
    "GrpcServer",
    "GrpcServiceConfig",
    "InferenceJob",
    "InferenceServicer",
    "InferenceWorker",
    "JobPriority",
    "JobStatus",
    "SimilarityResult",
]