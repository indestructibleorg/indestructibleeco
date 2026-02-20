"""Shared database layer — Supabase client wrapper + connection pool.

URI: indestructibleeco://backend/shared/db
"""

from .client import SupabaseClient, get_client

__all__ = ["SupabaseClient", "get_client"]
