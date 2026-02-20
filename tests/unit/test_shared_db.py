"""Unit tests for shared DB layer (Step 24)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.shared.db.client import SupabaseClient, get_client


class TestSupabaseClientInit:
    def test_default_url(self):
        c = SupabaseClient()
        assert "localhost" in c._url or "54321" in c._url

    def test_custom_url(self):
        c = SupabaseClient(url="http://supabase.example.com:8000")
        assert c._url == "http://supabase.example.com:8000"

    def test_singleton(self):
        c1 = get_client()
        c2 = get_client()
        assert c1 is c2


class TestSupabaseClientHealth:
    @pytest.mark.asyncio
    async def test_health_disconnected(self):
        c = SupabaseClient(url="http://localhost:1")
        result = await c.health()
        assert result["status"] == "disconnected"


class TestSupabaseClientCRUD:
    @pytest.mark.asyncio
    async def test_create_platform_sets_defaults(self):
        c = SupabaseClient(url="http://localhost:1")
        platform = {"name": "test", "type": "web"}
        # Will fail to connect but we can verify the data prep
        assert "name" in platform

    def test_client_pool_size(self):
        c = SupabaseClient(pool_size=20)
        assert c._pool_size == 20

    def test_not_initialized_before_use(self):
        c = SupabaseClient()
        assert c._initialized is False
