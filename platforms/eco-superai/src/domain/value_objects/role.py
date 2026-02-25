"""Role and Permission value objects for RBAC.

Defines the fine-grained permission model and the role hierarchy used by
the security infrastructure (:mod:`src.infrastructure.security`) to enforce
access control.  Every API endpoint ultimately delegates authorisation
checks to :class:`RolePermissions`.
"""
from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    """System permissions.

    Permissions follow a ``<resource>:<verb>`` naming convention so that they
    can be grouped and filtered programmatically.
    """

    # --- User management ---
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    USER_ADMIN = "user:admin"

    # --- Quantum computing ---
    QUANTUM_EXECUTE = "quantum:execute"
    QUANTUM_READ = "quantum:read"

    # --- AI / ML ---
    AI_EXECUTE = "ai:execute"
    AI_READ = "ai:read"
    AI_MANAGE = "ai:manage"

    # --- Scientific computing ---
    SCIENTIFIC_COMPUTE = "scientific:compute"
    SCIENTIFIC_EXECUTE = "scientific:execute"
    SCIENTIFIC_READ = "scientific:read"

    # --- Administration ---
    ADMIN_ACCESS = "admin:access"
    ADMIN_FULL = "admin:full"
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"

    # --- System ---
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_METRICS = "system:metrics"


class UserRole(str, Enum):
    """User roles with hierarchical permissions.

    Roles are ordered from most privileged (:attr:`ADMIN`) to least
    privileged (:attr:`VIEWER`).  The mapping from roles to concrete
    permissions lives in :class:`RolePermissions`.
    """

    ADMIN = "admin"
    OPERATOR = "operator"
    SCIENTIST = "scientist"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class RolePermissions:
    """Static mapping from :class:`UserRole` to sets of :class:`Permission`.

    This class is intentionally not instantiated; all methods are class-level
    so that the security layer can invoke them without managing state.
    """

    _ROLE_MAP: dict[UserRole, set[Permission]] = {
        UserRole.VIEWER: {
            Permission.USER_READ,
            Permission.QUANTUM_READ,
            Permission.AI_READ,
            Permission.SCIENTIFIC_READ,
        },
        UserRole.DEVELOPER: {
            Permission.USER_READ,
            Permission.USER_WRITE,
            Permission.QUANTUM_READ,
            Permission.QUANTUM_EXECUTE,
            Permission.AI_READ,
            Permission.AI_EXECUTE,
            Permission.SCIENTIFIC_READ,
            Permission.SCIENTIFIC_EXECUTE,
            Permission.SCIENTIFIC_COMPUTE,
        },
        UserRole.SCIENTIST: {
            Permission.USER_READ,
            Permission.USER_WRITE,
            Permission.QUANTUM_READ,
            Permission.QUANTUM_EXECUTE,
            Permission.AI_READ,
            Permission.AI_EXECUTE,
            Permission.AI_MANAGE,
            Permission.SCIENTIFIC_READ,
            Permission.SCIENTIFIC_EXECUTE,
            Permission.SCIENTIFIC_COMPUTE,
        },
        UserRole.OPERATOR: {
            Permission.USER_READ,
            Permission.USER_WRITE,
            Permission.QUANTUM_READ,
            Permission.QUANTUM_EXECUTE,
            Permission.AI_READ,
            Permission.AI_EXECUTE,
            Permission.AI_MANAGE,
            Permission.SCIENTIFIC_READ,
            Permission.SCIENTIFIC_EXECUTE,
            Permission.SCIENTIFIC_COMPUTE,
            Permission.SYSTEM_METRICS,
            Permission.ADMIN_ACCESS,
            Permission.ADMIN_AUDIT,
        },
        # Admin gets every permission defined in the enum.
        UserRole.ADMIN: set(Permission),
    }

    @classmethod
    def get_permissions(cls, role: UserRole) -> set[Permission]:
        """Return the full set of permissions granted to *role*."""
        return cls._ROLE_MAP.get(role, set())

    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Return ``True`` if *role* is granted *permission*."""
        return permission in cls.get_permissions(role)

    @classmethod
    def has_any_permission(cls, role: UserRole, permissions: set[Permission]) -> bool:
        """Return ``True`` if *role* holds at least one of *permissions*."""
        return bool(cls.get_permissions(role) & permissions)

    @classmethod
    def has_all_permissions(cls, role: UserRole, permissions: set[Permission]) -> bool:
        """Return ``True`` if *role* holds every permission in *permissions*."""
        return permissions.issubset(cls.get_permissions(role))
