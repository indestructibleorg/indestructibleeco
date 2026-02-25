"""Domain value objects — immutable, identity-less types."""
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.domain.value_objects.role import UserRole, Permission, RolePermissions

__all__ = ["Email", "HashedPassword", "UserRole", "Permission", "RolePermissions"]