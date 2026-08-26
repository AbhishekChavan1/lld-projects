"""
Object Pool Pattern - Database Connection Pool

Creating and destroying DB connections per request is expensive (~50-200ms).
Instead, maintain a pool of reusable connections. Borrow, use, return.

Use cases in LLD:
- Parking Lot: connection pool for shared DB across entry gates
- Job Scheduler: thread pool for concurrent job execution
- Cache: pool of Redis connections
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any


class PooledConnection:
    """
    A single connection managed by the pool.
    Tracks whether it's currently checked out.
    """

    def __init__(self, conn_id: int, host: str = "localhost", port: int = 5432) -> None:
        self.conn_id = conn_id
        self.host = host
        self.port = port
        self.in_use = False
        self.query_count = 0
        self.created_at = time.time()

    def execute(self, query: str) -> str:
        if not self.in_use:
            raise RuntimeError(f"Connection {self.conn_id} not checked out")
        self.query_count += 1
        return f"[Conn {self.conn_id}] Executed: {query}"

    def close(self) -> None:
        self.in_use = False

    def __repr__(self) -> str:
        status = "IN_USE" if self.in_use else "IDLE"
        return f"PooledConnection(id={self.conn_id}, status={status}, queries={self.query_count})"


class ConnectionPool:
    """
    Thread-safe connection pool with pre-warming and lazy growth.

    Pre-warms `min_size` connections on init. Grows up to `max_size`
    on demand. Blocks callers when pool is exhausted.
    """

    def __init__(
        self,
        max_size: int = 10,
        min_size: int = 3,
        host: str = "localhost",
        port: int = 5432,
    ) -> None:
        if min_size > max_size:
            raise ValueError("min_size cannot exceed max_size")

        self.max_size = max_size
        self.host = host
        self.port = port
        self._created_count = 0

        self._available: deque[PooledConnection] = deque()
        self._in_use: set[int] = set()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)

        self._pre_warm(min_size)

    def _pre_warm(self, count: int) -> None:
        for _ in range(count):
            conn = self._create_connection()
            self._available.append(conn)

    def _create_connection(self) -> PooledConnection:
        self._created_count += 1
        conn = PooledConnection(self._created_count, self.host, self.port)
        return conn

    def borrow(self, timeout: float | None = None) -> PooledConnection:
        """
        Borrow a connection from the pool.
        Blocks if pool is exhausted until one is returned or timeout.
        """
        with self._not_empty:
            deadline = time.monotonic() + timeout if timeout else None

            while True:
                if self._available:
                    conn = self._available.popleft()
                    conn.in_use = True
                    self._in_use.add(conn.conn_id)
                    return conn

                if self._created_count < self.max_size:
                    conn = self._create_connection()
                    conn.in_use = True
                    self._in_use.add(conn.conn_id)
                    return conn

                remaining = deadline - time.monotonic() if deadline else None
                if remaining is not None and remaining <= 0:
                    raise TimeoutError("Pool exhausted, no connection available")

                self._not_empty.wait(timeout=remaining)

    def release(self, conn: PooledConnection) -> None:
        """Return a connection to the pool."""
        with self._lock:
            conn.close()
            self._in_use.discard(conn.conn_id)
            self._available.append(conn)
            self._not_empty.notify()

    @property
    def available_count(self) -> int:
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        return len(self._in_use)

    @property
    def total_count(self) -> int:
        return self._created_count

    def __repr__(self) -> str:
        return (
            f"ConnectionPool(available={self.available_count}, "
            f"in_use={self.in_use_count}, total={self.total_count})"
        )
