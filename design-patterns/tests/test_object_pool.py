"""Tests for Object Pool Pattern implementations."""
import threading
import time
import pytest
from object_pool.connection_pool import ConnectionPool, PooledConnection
from object_pool.worker_pool import WorkerPool


class TestConnectionPool:
    """Tests for connection pool."""

    def test_pre_warms_connections(self):
        pool = ConnectionPool(max_size=5, min_size=3)
        assert pool.available_count == 3
        assert pool.total_count == 3

    def test_borrow_returns_connection(self):
        pool = ConnectionPool(max_size=5, min_size=2)
        conn = pool.borrow()
        assert isinstance(conn, PooledConnection)
        assert conn.in_use is True
        assert pool.in_use_count == 1
        assert pool.available_count == 1

    def test_release_returns_to_pool(self):
        pool = ConnectionPool(max_size=5, min_size=2)
        conn = pool.borrow()
        assert pool.available_count == 1
        pool.release(conn)
        assert conn.in_use is False
        assert pool.available_count == 2
        assert pool.in_use_count == 0

    def test_borrow_grows_pool(self):
        pool = ConnectionPool(max_size=5, min_size=2)
        assert pool.total_count == 2
        for _ in range(3):
            pool.borrow()
        assert pool.total_count == 3

    def test_borrow_fails_at_max(self):
        pool = ConnectionPool(max_size=3, min_size=1)
        pool.borrow()
        pool.borrow()
        pool.borrow()
        with pytest.raises(TimeoutError):
            pool.borrow(timeout=0.01)

    def test_execute_query(self):
        pool = ConnectionPool(max_size=3, min_size=1)
        conn = pool.borrow()
        result = conn.execute("SELECT 1")
        assert "SELECT 1" in result
        assert conn.query_count == 1

    def test_cannot_execute_without_checkout(self):
        conn = PooledConnection(1)
        with pytest.raises(RuntimeError, match="not checked out"):
            conn.execute("SELECT 1")

    def test_invalid_pool_config(self):
        with pytest.raises(ValueError, match="min_size cannot exceed max_size"):
            ConnectionPool(max_size=2, min_size=5)

    def test_thread_safety(self):
        pool = ConnectionPool(max_size=5, min_size=2)
        results = []

        def borrow_and_release():
            conn = pool.borrow()
            conn.execute("SELECT 1")
            time.sleep(0.01)
            pool.release(conn)
            results.append(conn.conn_id)

        threads = [threading.Thread(target=borrow_and_release) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        assert pool.available_count == 5


class TestWorkerPool:
    """Tests for worker pool."""

    def test_start_creates_workers(self):
        pool = WorkerPool(pool_size=4)
        pool.start()
        assert len(pool.get_workers()) == 4
        pool.shutdown()

    def test_submit_executes_task(self):
        pool = WorkerPool(pool_size=2)
        pool.start()
        result = []

        pool.submit("task1", lambda: result.append("done"))
        pool.shutdown(wait=True)

        assert "done" in result

    def test_multiple_tasks(self):
        pool = WorkerPool(pool_size=2)
        pool.start()
        results = []

        for i in range(5):
            pool.submit(f"task{i}", lambda idx=i: results.append(idx))
        pool.shutdown(wait=True)

        assert len(results) == 5

    def test_shutdown_rejects_new_tasks(self):
        pool = WorkerPool(pool_size=2)
        pool.start()
        pool.shutdown(wait=True)
        with pytest.raises(RuntimeError, match="shutdown"):
            pool.submit("task", lambda: None)

    def test_completed_count(self):
        pool = WorkerPool(pool_size=2)
        pool.start()

        for _ in range(3):
            pool.submit("task", lambda: time.sleep(0.01))
        pool.shutdown(wait=True)

        assert pool.completed_count == 3
