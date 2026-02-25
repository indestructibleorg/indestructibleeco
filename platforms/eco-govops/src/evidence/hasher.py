"""Cryptographic hashing utilities for the Evidence Layer.

Provides ``EvidenceHasher`` — a stateless helper that creates deterministic,
content-addressable hashes of arbitrary payloads and files.  Three algorithms
are supported out of the box: SHA-256, SHA-512, and BLAKE2b.

Every hash result is wrapped in a ``SignedHash`` Pydantic model that records
the algorithm, hex digest, timestamp, and (optional) signer identity so
downstream consumers can verify provenance without additional lookups.

GL-governed: GL20-29 (data integrity / evidence layer)
"""
from __future__ import annotations

import enum
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Union

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
_CHUNK_SIZE: int = 8192  # bytes read at a time when hashing files


class HashAlgorithm(str, enum.Enum):
    """Supported cryptographic hash algorithms."""

    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"


class SignedHash(BaseModel):
    """Immutable record of a computed hash with provenance metadata.

    Attributes:
        algorithm: The hash algorithm that produced the digest.
        hex_digest: The lowercase hexadecimal representation of the hash.
        signed_at: UTC timestamp when the hash was computed.
        signer_id: Optional identifier of the entity that requested the hash
            (e.g. a service account, user principal, or CI job ID).
        content_length: Length in bytes of the hashed content (informational).
    """

    algorithm: HashAlgorithm
    hex_digest: str = Field(min_length=1)
    signed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    signer_id: str | None = None
    content_length: int = Field(ge=0, default=0)

    model_config = {"frozen": True}

    # -- convenience ---------------------------------------------------------

    def as_urn(self) -> str:
        """Return an RFC-6920-style ``ni:///`` URN for content addressing.

        Example: ``ni:///sha256;e3b0c44298fc1c149afb...``
        """
        return f"ni:///{self.algorithm.value};{self.hex_digest}"


# ---------------------------------------------------------------------------
# Core hasher
# ---------------------------------------------------------------------------


class EvidenceHasher:
    """Creates and verifies cryptographic hashes of evidence payloads.

    The hasher is stateless; every public method is self-contained and can be
    called concurrently from multiple threads.

    Usage::

        hasher = EvidenceHasher(default_algorithm=HashAlgorithm.SHA256)
        signed = hasher.hash_content(b"some evidence bytes", signer_id="ci-bot")
        assert hasher.verify_hash(b"some evidence bytes", signed)
    """

    def __init__(
        self,
        default_algorithm: HashAlgorithm = HashAlgorithm.SHA256,
        default_signer_id: str | None = None,
    ) -> None:
        self._default_algorithm = default_algorithm
        self._default_signer_id = default_signer_id
        logger.info(
            "evidence_hasher_initialised",
            default_algorithm=default_algorithm.value,
            default_signer_id=default_signer_id,
        )

    # -- public API ----------------------------------------------------------

    def hash_content(
        self,
        content: Union[bytes, str],
        *,
        algorithm: HashAlgorithm | None = None,
        signer_id: str | None = None,
    ) -> SignedHash:
        """Hash arbitrary bytes or a UTF-8 string and return a ``SignedHash``.

        Parameters:
            content: Raw bytes or a string to hash.  Strings are encoded to
                UTF-8 before hashing.
            algorithm: Override the default algorithm for this call.
            signer_id: Override the default signer for this call.

        Returns:
            A ``SignedHash`` capturing the digest and metadata.
        """
        algo = algorithm or self._default_algorithm
        raw = content.encode("utf-8") if isinstance(content, str) else content
        digest = self._compute_digest(raw, algo)
        signer = signer_id or self._default_signer_id

        signed = SignedHash(
            algorithm=algo,
            hex_digest=digest,
            signer_id=signer,
            content_length=len(raw),
        )
        logger.debug(
            "content_hashed",
            algorithm=algo.value,
            digest_prefix=digest[:16],
            content_length=len(raw),
        )
        return signed

    def hash_file(
        self,
        path: Union[str, Path],
        *,
        algorithm: HashAlgorithm | None = None,
        signer_id: str | None = None,
    ) -> SignedHash:
        """Stream-hash a file on disk and return a ``SignedHash``.

        Large files are read in ``_CHUNK_SIZE`` chunks to keep memory usage
        constant regardless of file size.

        Parameters:
            path: Filesystem path to the file.
            algorithm: Override the default algorithm for this call.
            signer_id: Override the default signer for this call.

        Returns:
            A ``SignedHash`` capturing the digest and metadata.

        Raises:
            FileNotFoundError: If *path* does not exist.
            IsADirectoryError: If *path* is a directory.
        """
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")
        if file_path.is_dir():
            raise IsADirectoryError(f"Expected a file, got directory: {file_path}")

        algo = algorithm or self._default_algorithm
        hasher_obj = self._make_hasher(algo)
        total_bytes = 0

        with file_path.open("rb") as fh:
            while True:
                chunk = fh.read(_CHUNK_SIZE)
                if not chunk:
                    break
                hasher_obj.update(chunk)
                total_bytes += len(chunk)

        digest = hasher_obj.hexdigest()
        signer = signer_id or self._default_signer_id

        signed = SignedHash(
            algorithm=algo,
            hex_digest=digest,
            signer_id=signer,
            content_length=total_bytes,
        )
        logger.debug(
            "file_hashed",
            path=str(file_path),
            algorithm=algo.value,
            digest_prefix=digest[:16],
            content_length=total_bytes,
        )
        return signed

    def verify_hash(
        self,
        content: Union[bytes, str],
        expected: SignedHash,
    ) -> bool:
        """Recompute the hash of *content* and compare to *expected*.

        Parameters:
            content: The original payload (bytes or string).
            expected: A previously computed ``SignedHash`` to verify against.

        Returns:
            ``True`` if the freshly computed digest matches the expected one.
        """
        raw = content.encode("utf-8") if isinstance(content, str) else content
        digest = self._compute_digest(raw, expected.algorithm)
        matches = digest == expected.hex_digest
        if not matches:
            logger.warning(
                "hash_verification_failed",
                algorithm=expected.algorithm.value,
                expected_prefix=expected.hex_digest[:16],
                actual_prefix=digest[:16],
            )
        else:
            logger.debug(
                "hash_verification_passed",
                algorithm=expected.algorithm.value,
                digest_prefix=digest[:16],
            )
        return matches

    def verify_file(
        self,
        path: Union[str, Path],
        expected: SignedHash,
    ) -> bool:
        """Recompute the hash of a file and compare to *expected*.

        Parameters:
            path: Filesystem path to the file.
            expected: A previously computed ``SignedHash`` to verify against.

        Returns:
            ``True`` if the freshly computed digest matches the expected one.
        """
        current = self.hash_file(path, algorithm=expected.algorithm)
        matches = current.hex_digest == expected.hex_digest
        if not matches:
            logger.warning(
                "file_hash_verification_failed",
                path=str(path),
                algorithm=expected.algorithm.value,
                expected_prefix=expected.hex_digest[:16],
                actual_prefix=current.hex_digest[:16],
            )
        return matches

    def hash_dict(
        self,
        data: dict[str, Any],
        *,
        algorithm: HashAlgorithm | None = None,
        signer_id: str | None = None,
    ) -> SignedHash:
        """Deterministically hash a JSON-serialisable dictionary.

        Keys are sorted recursively so that logically equivalent dicts always
        produce the same digest.

        Parameters:
            data: A JSON-serialisable dictionary.
            algorithm: Override the default algorithm for this call.
            signer_id: Override the default signer for this call.

        Returns:
            A ``SignedHash`` capturing the digest and metadata.
        """
        import json

        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
        return self.hash_content(
            canonical.encode("utf-8"),
            algorithm=algorithm,
            signer_id=signer_id,
        )

    # -- internals -----------------------------------------------------------

    @staticmethod
    def _make_hasher(algorithm: HashAlgorithm) -> "hashlib._Hash":
        """Return a fresh ``hashlib`` hasher for the given algorithm."""
        if algorithm is HashAlgorithm.SHA256:
            return hashlib.sha256()
        if algorithm is HashAlgorithm.SHA512:
            return hashlib.sha512()
        if algorithm is HashAlgorithm.BLAKE2B:
            return hashlib.blake2b()
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    @classmethod
    def _compute_digest(cls, data: bytes, algorithm: HashAlgorithm) -> str:
        """One-shot hash and return the hex digest."""
        h = cls._make_hasher(algorithm)
        h.update(data)
        return h.hexdigest()
