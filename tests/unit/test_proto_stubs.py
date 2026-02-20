"""Unit tests for gRPC proto stubs (Step 25)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.shared.proto.generated.ai_service_pb2 import (
    GenerateRequest, GenerateResponse, StreamChunk,
    EmbeddingRequest, EmbeddingResponse,
    HealthCheckRequest, HealthCheckResponse,
)
from backend.shared.proto.generated.yaml_governance_pb2 import (
    ValidateRequest, ValidateResponse, ValidationError,
    StampRequest, StampResponse,
)


class TestAIServiceProto:
    def test_generate_request_defaults(self):
        req = GenerateRequest()
        assert req.max_tokens == 512
        assert req.temperature == 0.7

    def test_generate_request_custom(self):
        req = GenerateRequest(model_id="llama-3.1-8b", prompt="hello", max_tokens=100)
        assert req.model_id == "llama-3.1-8b"
        assert req.max_tokens == 100

    def test_generate_response(self):
        resp = GenerateResponse(request_id="r1", text="world", model_id="m1")
        assert resp.finish_reason == "stop"

    def test_stream_chunk(self):
        chunk = StreamChunk(request_id="r1", delta="tok", index=0)
        assert chunk.delta == "tok"

    def test_embedding_request(self):
        req = EmbeddingRequest(texts=["hello", "world"])
        assert len(req.texts) == 2
        assert req.dimensions == 1024

    def test_embedding_response(self):
        resp = EmbeddingResponse(embeddings=[[1.0, 2.0]], dimensions=2)
        assert len(resp.embeddings) == 1

    def test_health_check(self):
        req = HealthCheckRequest(service="ai")
        resp = HealthCheckResponse()
        assert resp.status == "SERVING"


class TestYAMLGovernanceProto:
    def test_validate_request(self):
        req = ValidateRequest(content="test: yaml")
        assert req.strict is True

    def test_validate_response(self):
        err = ValidationError(path="root", message="missing block")
        resp = ValidateResponse(valid=False, errors=[err])
        assert len(resp.errors) == 1

    def test_stamp_request(self):
        req = StampRequest(name="my-svc", namespace="prod")
        assert req.kind == "Deployment"

    def test_stamp_response(self):
        resp = StampResponse(unique_id="abc", uri="indestructibleeco://test")
        assert resp.uri.startswith("indestructibleeco://")
