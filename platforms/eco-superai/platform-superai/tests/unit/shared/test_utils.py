"""Unit tests for shared utilities."""
from __future__ import annotations

from datetime import datetime, timezone

from src.shared.utils import (
    generate_id,
    generate_short_id,
    utc_now,
    to_iso,
    from_iso,
    sha256_hex,
    paginate_params,
    paginate_response,
    truncate,
    snake_to_camel,
    camel_to_snake,
    compact_dict,
    deep_merge,
)


class TestIDGeneration:
    def test_generate_id_format(self):
        uid = generate_id()
        assert len(uid) == 36
        assert uid.count("-") == 4

    def test_generate_id_unique(self):
        ids = {generate_id() for _ in range(100)}
        assert len(ids) == 100

    def test_generate_short_id_with_prefix(self):
        sid = generate_short_id("usr")
        assert sid.startswith("usr-")
        assert len(sid) == 12  # "usr-" + 8 hex chars

    def test_generate_short_id_no_prefix(self):
        sid = generate_short_id()
        assert len(sid) == 8


class TestDateTime:
    def test_utc_now_is_aware(self):
        now = utc_now()
        assert now.tzinfo is not None

    def test_to_iso_and_back(self):
        now = utc_now()
        iso = to_iso(now)
        assert iso is not None
        parsed = from_iso(iso)
        assert parsed.year == now.year

    def test_to_iso_none(self):
        assert to_iso(None) is None


class TestHashing:
    def test_sha256_deterministic(self):
        h1 = sha256_hex("hello")
        h2 = sha256_hex("hello")
        assert h1 == h2
        assert len(h1) == 64

    def test_sha256_different_inputs(self):
        assert sha256_hex("a") != sha256_hex("b")


class TestPagination:
    def test_paginate_params_defaults(self):
        skip, limit = paginate_params()
        assert skip == 0
        assert limit == 20

    def test_paginate_params_clamp(self):
        skip, limit = paginate_params(skip=-5, limit=500)
        assert skip == 0
        assert limit == 100

    def test_paginate_response(self):
        resp = paginate_response(items=[1, 2, 3], total=10, skip=0, limit=3)
        assert resp["has_next"] is True
        assert resp["total_pages"] == 4

    def test_paginate_response_last_page(self):
        resp = paginate_response(items=[10], total=10, skip=9, limit=1)
        assert resp["has_next"] is False


class TestStringHelpers:
    def test_truncate_short(self):
        assert truncate("hello", 10) == "hello"

    def test_truncate_long(self):
        result = truncate("a" * 300, 200)
        assert len(result) == 200
        assert result.endswith("...")

    def test_snake_to_camel(self):
        assert snake_to_camel("hello_world") == "helloWorld"
        assert snake_to_camel("user_id") == "userId"

    def test_camel_to_snake(self):
        assert camel_to_snake("helloWorld") == "hello_world"
        assert camel_to_snake("userId") == "user_id"


class TestDictHelpers:
    def test_compact_dict(self):
        result = compact_dict({"a": 1, "b": None, "c": 0, "d": None})
        assert result == {"a": 1, "c": 0}

    def test_deep_merge(self):
        base = {"a": 1, "b": {"x": 10, "y": 20}}
        override = {"b": {"y": 99, "z": 30}, "c": 3}
        result = deep_merge(base, override)
        assert result == {"a": 1, "b": {"x": 10, "y": 99, "z": 30}, "c": 3}

    def test_deep_merge_no_mutation(self):
        base = {"a": {"b": 1}}
        override = {"a": {"c": 2}}
        deep_merge(base, override)
        assert "c" not in base["a"]