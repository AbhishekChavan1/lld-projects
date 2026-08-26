"""Tests for Singleton Pattern implementations."""
import threading
import pytest
from singleton.metaclass_singleton import DatabaseConnection, SingletonMeta
from singleton.logger_singleton import Logger, LogLevel
from singleton.config_singleton import AppConfig


class TestMetaclassSingleton:
    """Tests for metaclass-based singleton."""

    def setup_method(self):
        SingletonMeta.clear_instance(DatabaseConnection)

    def test_same_instance(self):
        db1 = DatabaseConnection("host1", 5432, "db1")
        db2 = DatabaseConnection("host2", 9999, "db2")
        assert db1 is db2

    def test_first_init_params_persist(self):
        db1 = DatabaseConnection("host1", 5432, "db1")
        db2 = DatabaseConnection("host2", 9999, "db2")
        assert db1.host == "host1"
        assert db1.port == 5432
        assert db1.db == "db1"

    def test_shared_query_count(self):
        db1 = DatabaseConnection()
        db2 = DatabaseConnection()
        db1.execute("SELECT 1")
        db2.execute("SELECT 2")
        assert db1.query_count == 2
        assert db2.query_count == 2

    def test_thread_safety(self):
        SingletonMeta.clear_instance(DatabaseConnection)
        instances = []

        def create_instance():
            instances.append(DatabaseConnection("t", 1, "t"))

        threads = [threading.Thread(target=create_instance) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(inst is instances[0] for inst in instances)


class TestLoggerSingleton:
    """Tests for logger singleton."""

    def setup_method(self):
        Logger.reset()

    def test_same_instance(self):
        l1 = Logger()
        l2 = Logger()
        assert l1 is l2

    def test_min_level_from_first_init(self):
        l1 = Logger(LogLevel.DEBUG)
        l2 = Logger(LogLevel.ERROR)
        assert l2.min_level == LogLevel.DEBUG

    def test_log_counting(self):
        logger = Logger()
        logger.info("msg1")
        logger.error("msg2")
        logger.debug("msg3")
        assert logger.log_count == 3

    def test_stored_logs(self):
        logger = Logger()
        logger.info("hello")
        logger.warning("world")
        logs = logger.get_logs()
        assert len(logs) == 2
        assert "hello" in logs[0]
        assert "world" in logs[1]


class TestAppConfigSingleton:
    """Tests for config singleton."""

    def setup_method(self):
        AppConfig.reset()

    def test_same_instance(self):
        c1 = AppConfig()
        c2 = AppConfig()
        assert c1 is c2

    def test_shared_state(self):
        c1 = AppConfig()
        c1.set("key", "value")
        c2 = AppConfig()
        assert c2.get("key") == "value"

    def test_defaults(self):
        config = AppConfig()
        assert config.get("debug") is False
        assert config.get("max_retries") == 3
        assert config.get("timeout_seconds") == 30

    def test_override_default(self):
        config = AppConfig()
        config.set("debug", True)
        assert config.get("debug") is True
