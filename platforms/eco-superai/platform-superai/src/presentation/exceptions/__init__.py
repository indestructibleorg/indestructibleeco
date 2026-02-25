"""Exception handlers — map domain/infrastructure exceptions to HTTP responses."""
from src.presentation.exceptions.handlers import register_exception_handlers

__all__ = ["register_exception_handlers"]
