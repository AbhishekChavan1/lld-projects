"""
Singleton Pattern - App Config Implementation

Global configuration loaded once from environment/files.
Multiple components (PaymentService, NotificationService, etc.)
all read from the same config instance.

This is the most common singleton use case in LLD projects.
"""
from __future__ import annotations

import threading
from typing import Any


class AppConfig:
    """
    Singleton application configuration.

    Usage:
        config = AppConfig()
        config.set("max_retries", 3)
        retries = config.get("max_retries")
    """

    _instance: AppConfig | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> AppConfig:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, initial_config: dict[str, Any] | None = None) -> None:
        if self._initialized:
            return
        self._config: dict[str, Any] = initial_config or {}
        self._defaults: dict[str, Any] = {
            "debug": False,
            "max_retries": 3,
            "timeout_seconds": 30,
            "log_level": "INFO",
        }
        self._initialized = True

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, self._defaults.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get_all(self) -> dict[str, Any]:
        merged = {**self._defaults, **self._config}
        return dict(merged)

    def update(self, settings: dict[str, Any]) -> None:
        self._config.update(settings)

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    def __repr__(self) -> str:
        return f"AppConfig({self.get_all()})"
