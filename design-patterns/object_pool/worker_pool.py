"""
Object Pool Pattern - Worker/Thread Pool

A pool of reusable worker threads for concurrent task execution.
Instead of spawning a new thread per task (expensive), reuse
a fixed set of workers from the pool.

Use cases in LLD:
- Job Scheduler: pool of workers processing scheduled jobs
- Notification Service: pool of senders for email/SMS
- Rate Limiter: pool of async handlers
"""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable


class Worker:
    """A single worker thread that processes tasks from a queue."""

    def __init__(self, worker_id: int) -> None:
        self.worker_id = worker_id
        self.busy = False
        self.tasks_completed = 0
        self._current_task: str | None = None

    def __repr__(self) -> str:
        status = "BUSY" if self.busy else "IDLE"
        return f"Worker(id={self.worker_id}, status={status}, completed={self.tasks_completed})"


class WorkerPool:
    """
    Fixed-size pool of worker threads with a shared task queue.

    Tasks are submitted via submit() and executed by the next
    available worker. Workers block on the queue when idle.
    """

    def __init__(self, pool_size: int = 4) -> None:
        self.pool_size = pool_size
        self._workers: list[Worker] = [Worker(i) for i in range(pool_size)]
        self._task_queue: deque[tuple[str, Callable[..., Any], tuple[Any, ...]]] = deque()
        self._lock = threading.Lock()
        self._task_available = threading.Condition(self._lock)
        self._shutdown = False
        self._threads: list[threading.Thread] = []
        self._started = False
        self._completed_count = 0

    def start(self) -> None:
        """Start worker threads."""
        if self._started:
            return
        self._started = True
        for i in range(self.pool_size):
            t = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            self._threads.append(t)
            t.start()

    def _worker_loop(self, worker_id: int) -> None:
        worker = self._workers[worker_id]
        while True:
            with self._task_available:
                while not self._task_queue and not self._shutdown:
                    self._task_available.wait(timeout=0.5)

                if not self._task_queue:
                    return

                task_name, func, args = self._task_queue.popleft()
                worker.busy = True
                worker._current_task = task_name
            try:
                func(*args)
            except Exception:
                pass
            finally:
                with self._lock:
                    worker.busy = False
                    worker._current_task = None
                    worker.tasks_completed += 1
                    self._completed_count += 1

    def submit(self, task_name: str, func: Callable[..., Any], *args: Any) -> None:
        """Submit a task to the pool queue."""
        if self._shutdown:
            raise RuntimeError("Pool is shutdown")
        with self._task_available:
            self._task_queue.append((task_name, func, args))
            self._task_available.notify()

    def shutdown(self, wait: bool = True) -> None:
        """Shutdown the pool, finishing pending tasks."""
        with self._lock:
            self._shutdown = True
            self._task_available.notify_all()
        if wait:
            for t in self._threads:
                t.join(timeout=5)

    @property
    def busy_count(self) -> int:
        return sum(1 for w in self._workers if w.busy)

    @property
    def idle_count(self) -> int:
        return sum(1 for w in self._workers if not w.busy)

    @property
    def pending_count(self) -> int:
        return len(self._task_queue)

    @property
    def completed_count(self) -> int:
        return self._completed_count

    def get_workers(self) -> list[Worker]:
        return list(self._workers)

    def __repr__(self) -> str:
        return (
            f"WorkerPool(size={self.pool_size}, busy={self.busy_count}, "
            f"pending={self.pending_count}, completed={self.completed_count})"
        )
