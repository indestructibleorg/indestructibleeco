"""Unit tests for API schemas validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.presentation.api.schemas import (
    UserCreateRequest,
    UserUpdateRequest,
    TokenRequest,
    QuantumJobRequest,
    AIExpertCreateRequest,
    ScientificMatrixRequest,
)


class TestUserSchemas:
    def test_valid_user_create(self):
        req = UserCreateRequest(
            username="john_doe",
            email="john@example.com",
            password="SecureP@ss1",
            full_name="John Doe",
            role="developer",
        )
        assert req.username == "john_doe"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(username="ab", email="a@b.com", password="SecureP@ss1")

    def test_username_invalid_chars(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(username="bad user!", email="a@b.com", password="SecureP@ss1")

    def test_invalid_role(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(username="test", email="a@b.com", password="SecureP@ss1", role="superadmin")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreateRequest(username="test", email="a@b.com", password="short")

    def test_user_update_partial(self):
        req = UserUpdateRequest(full_name="New Name")
        assert req.full_name == "New Name"
        assert req.role is None

    def test_token_request(self):
        req = TokenRequest(username="test", password="pass")
        assert req.username == "test"


class TestQuantumSchemas:
    def test_valid_quantum_job(self):
        req = QuantumJobRequest(num_qubits=4, algorithm="bell", shots=500)
        assert req.num_qubits == 4

    def test_qubits_out_of_range(self):
        with pytest.raises(ValidationError):
            QuantumJobRequest(num_qubits=0, algorithm="bell")
        with pytest.raises(ValidationError):
            QuantumJobRequest(num_qubits=31, algorithm="bell")

    def test_shots_range(self):
        with pytest.raises(ValidationError):
            QuantumJobRequest(num_qubits=2, algorithm="bell", shots=0)
        with pytest.raises(ValidationError):
            QuantumJobRequest(num_qubits=2, algorithm="bell", shots=200000)


class TestAISchemas:
    def test_expert_create(self):
        req = AIExpertCreateRequest(name="Quantum Expert", domain="quantum")
        assert req.name == "Quantum Expert"
        assert req.temperature == 0.7

    def test_temperature_range(self):
        with pytest.raises(ValidationError):
            AIExpertCreateRequest(name="test", domain="test", temperature=3.0)


class TestScientificSchemas:
    def test_matrix_request(self):
        req = ScientificMatrixRequest(
            matrix=[[1.0, 2.0], [3.0, 4.0]], operation="determinant"
        )
        assert len(req.matrix) == 2
