"""
Singleton Pattern - Logger Implementation (Practical LLD Example)

A centralized logger ensuring no interleaved log output across threads.
In LLD problems like Notification Service or Job Scheduler, multiple
components write logs concurrently. A singleton logger serializes writes
to a single queue, preventing garbled output.
"""
from __future__ import annotations

import threading
import time
from enum import Enum
from typing import TextIO


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Logger:
    """
    Thread-safe singleton logger.

    Usage:
        logger = Logger()
        logger.info("User logged in")
        logger.error("Connection failed")
    """

    _instance: Logger | None = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> Logger:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(
        self,
        min_level: LogLevel = LogLevel.DEBUG,
        output: TextIO | None = None,
    ) -> None:
        if self._initialized:
            return
        self.min_level = min_level
        self.output = output
        self._buffer: list[str] = []
        self._buffer_lock = threading.Lock()
        self._initialized = True
        self._log_count = 0

    def _format(self, level: LogLevel, message: str) -> str:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] [{level.value}] {message}"

    def _log(self, level: LogLevel, message: str) -> None:
        if level.value < self.min_level.value:
            return
        formatted = self._format(level, message)
        with self._buffer_lock:
            self._log_count += 1
            self._buffer.append(formatted)
        if self.output:
            self.output.write(formatted + "\n")
        else:
            print(formatted)

    def debug(self, message: str) -> None:
        self._log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self._log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self._log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self._log(LogLevel.ERROR, message)

    def get_logs(self) -> list[str]:
        with self._buffer_lock:
            return list(self._buffer)

    @property
    def log_count(self) -> int:
        return self._log_count

    @classmethod
    def reset(cls) -> None:
        """Reset singleton (for testing only)."""
        cls._instance = None

    def __repr__(self) -> str:
        return f"Logger(level={self.min_level.value}, logs={self._log_count})"
