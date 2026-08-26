"""
Prototype Pattern - User Permission Prototype

Demonstrates cloning pre-configured permission templates.
Admin and Regular users share a base template but are customized
per instance. This is a common pattern in LLD for:
- User authorization registries
- Role-based access control
- Feature flag configurations
"""
from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"


class UserPrototype(ABC):
    """
    Abstract Prototype interface for user templates.
    """

    @abstractmethod
    def clone(self) -> UserPrototype:
        """Create a deep copy of this user template."""
        ...

    @abstractmethod
    def get_permissions(self) -> set[Permission]:
        ...


class AdminUser(UserPrototype):
    """Admin user template with full permissions."""

    def __init__(self) -> None:
        self.role = "admin"
        self.permissions: set[Permission] = {
            Permission.READ,
            Permission.WRITE,
            Permission.DELETE,
            Permission.ADMIN,
        }
        self.settings: dict[str, Any] = {
            "two_factor": True,
            "session_timeout": 3600,
            "can_manage_users": True,
        }

    def clone(self) -> AdminUser:
        """Clone admin template with all permissions."""
        return copy.deepcopy(self)

    def get_permissions(self) -> set[Permission]:
        return self.permissions.copy()

    def add_permission(self, perm: Permission) -> None:
        self.permissions.add(perm)

    def remove_permission(self, perm: Permission) -> None:
        self.permissions.discard(perm)

    def update_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value

    def __repr__(self) -> str:
        perms = {p.value for p in self.permissions}
        return f"AdminUser(role='{self.role}', permissions={perms})"


class RegularUser(UserPrototype):
    """Regular user template with read-only permissions."""

    def __init__(self) -> None:
        self.role = "regular"
        self.permissions: set[Permission] = {Permission.READ}
        self.settings: dict[str, Any] = {
            "two_factor": False,
            "session_timeout": 1800,
            "can_manage_users": False,
        }

    def clone(self) -> RegularUser:
        """Clone regular user template."""
        return copy.deepcopy(self)

    def get_permissions(self) -> set[Permission]:
        return self.permissions.copy()

    def add_permission(self, perm: Permission) -> None:
        self.permissions.add(perm)

    def update_setting(self, key: str, value: Any) -> None:
        self.settings[key] = value

    def __repr__(self) -> str:
        perms = {p.value for p in self.permissions}
        return f"RegularUser(role='{self.role}', permissions={perms})"


class UserPrototypeRegistry:
    """
    Registry that stores and retrieves user prototypes.
    Clients register templates once, then request clones
    instead of building users from scratch.
    """

    def __init__(self) -> None:
        self._prototypes: dict[str, UserPrototype] = {}

    def register(self, name: str, prototype: UserPrototype) -> None:
        self._prototypes[name] = prototype

    def unregister(self, name: str) -> None:
        self._prototypes.pop(name, None)

    def create(self, name: str) -> UserPrototype:
        prototype = self._prototypes.get(name)
        if prototype is None:
            raise KeyError(f"No prototype registered with name '{name}'")
        return prototype.clone()

    def list_prototypes(self) -> list[str]:
        return list(self._prototypes.keys())
