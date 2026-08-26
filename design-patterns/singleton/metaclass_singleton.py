"""
Singleton Pattern - Metaclass Implementation (Most Pythonic)

Ensures a class has exactly ONE instance and provides a global point of access.

Use cases in LLD:
- Database connection pools
- Thread managers
- Centralized registries

The metaclass approach is the most Pythonic because it intercepts
class creation at the type level, making __init__ safe from duplicate calls.
"""
from __future__ import annotations

import threading
from typing import Any


class SingletonMeta(type):
    """
    Thread-safe Singleton metaclass.

    When a class uses this metaclass, the first time the class is instantiated,
    the instance is cached. Subsequent instantiations return the cached instance.
    """

    _instances: dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]

    @classmethod
    def clear_instance(mcs, cls: type) -> None:
        """Remove cached instance (useful for testing)."""
        with mcs._lock:
            mcs._instances.pop(cls, None)


class DatabaseConnection(metaclass=SingletonMeta):
    """
    Singleton database connection pool.

    In a real LLD project like a Parking Lot, multiple entry gates
    would all share this single connection pool. Without singleton,
    each gate creating its own pool would waste connections and
    cause inconsistent state.
    """

    def __init__(self, host: str = "localhost", port: int = 5432, db: str = "lld_db"):
        self.host = host
        self.port = port
        self.db = db
        self._connected = False
        self._query_count = 0
        self._connect()

    def _connect(self) -> None:
        print(f"[DB] Connecting to {self.host}:{self.port}/{self.db}...")
        self._connected = True

    def execute(self, query: str) -> str:
        if not self._connected:
            raise RuntimeError("Not connected to database")
        self._query_count += 1
        return f"[DB] Executed query #{self._query_count}: {query}"

    @property
    def query_count(self) -> int:
        return self._query_count

    @property
    def is_connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        return (
            f"DatabaseConnection(host='{self.host}', port={self.port}, "
            f"db='{self.db}', queries={self._query_count})"
        )
