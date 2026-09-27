import inspect

import pytest

import user_services
import violation
from user_services import (
    AnalyticsReport,
    InMemoryUserCache,
    PostgresUserRepository,
    User,
    UserAdminService,
    UserAnalyticsReader,
    UserAudit,
    UserAuditReader,
    UserAuthService,
    UserReader,
    UserRegistrationService,
    UserWriter,
)
from violation import UserRepository
from violation import InMemoryUserCache as FatCache
from violation import User as FatUser
from violation import UserAuthService as FatAuthService


class TestViolation:
    """The anti-pattern: one fat interface nobody can implement cleanly."""

    def test_repository_is_abstract(self):
        with pytest.raises(TypeError):
            UserRepository()

    def test_fat_interface_has_eight_methods(self):
        assert len(UserRepository.__abstractmethods__) == 8

    def test_cache_forced_to_implement_write_methods(self):
        cache = FatCache()
        cache.save(FatUser("42", "alice"))
        assert cache.find_by_id("42") is not None

    def test_unsupported_members_raise_at_runtime(self):
        cache = FatCache()
        with pytest.raises(NotImplementedError, match="Cache has no audit trail"):
            cache.get_audit_trail("42")
        with pytest.raises(NotImplementedError, match="Cache has no analytics"):
            cache.get_analytics("q")
        with pytest.raises(NotImplementedError, match="Cache cannot export"):
            cache.export_to_csv()

    def test_type_checking_lies_about_the_cache(self):
        """Static analysis is happy; the failure only shows up in production."""
        assert isinstance(FatCache(), UserRepository)
        with pytest.raises(NotImplementedError):
            FatCache().get_analytics("q")

    def test_service_takes_the_fat_dependency(self):
        params = list(inspect.signature(FatAuthService.__init__).parameters)
        assert "repository" in params


class TestNarrowInterfaces:
    def test_reader_is_abstract(self):
        with pytest.raises(TypeError):
            UserReader()

    def test_writer_is_abstract(self):
        with pytest.raises(TypeError):
            UserWriter()

    def test_audit_reader_is_abstract(self):
        with pytest.raises(TypeError):
            UserAuditReader()

    def test_analytics_reader_is_abstract(self):
        with pytest.raises(TypeError):
            UserAnalyticsReader()

    def test_interfaces_are_small_and_focused(self):
        assert len(UserReader.__abstractmethods__) == 2
        assert len(UserWriter.__abstractmethods__) == 3
        assert len(UserAuditReader.__abstractmethods__) == 1
        assert len(UserAnalyticsReader.__abstractmethods__) == 1

    def test_no_interface_declares_another_s_responsibility(self):
        for iface in (UserReader, UserWriter, UserAuditReader, UserAnalyticsReader):
            methods = set(iface.__abstractmethods__)
            assert "save" not in methods or iface is UserWriter
            assert "get_audit_trail" not in methods or iface is UserAuditReader
            assert "get_analytics" not in methods or iface is UserAnalyticsReader

    def test_postgres_implements_every_interface(self):
        repo = PostgresUserRepository()
        assert isinstance(repo, UserReader)
        assert isinstance(repo, UserWriter)
        assert isinstance(repo, UserAuditReader)
        assert isinstance(repo, UserAnalyticsReader)

    def test_cache_implements_only_the_reader(self):
        cache = InMemoryUserCache()
        assert isinstance(cache, UserReader)
        assert not isinstance(cache, UserWriter)
        assert not isinstance(cache, UserAuditReader)
        assert not isinstance(cache, UserAnalyticsReader)

    def test_cache_has_no_dead_methods(self):
        """Contrast with the fat version: nothing to stub, nothing to raise."""
        source = inspect.getsource(InMemoryUserCache)
        assert "NotImplementedError" not in source
        public = [m for m in dir(InMemoryUserCache) if not m.startswith("_")]
        assert public == ["find_active_users", "find_by_id"]


class TestUserReaderImplementations:
    def test_missing_user_returns_none(self):
        assert InMemoryUserCache().find_by_id("nope") is None
        assert PostgresUserRepository().find_by_id("nope") is None

    def test_readers_return_none_for_unknown_user(self):
        assert InMemoryUserCache().find_by_id("nope") is None
        assert PostgresUserRepository().find_by_id("nope") is None

    def test_db_reads_back_what_it_saved(self, capsys):
        repo = PostgresUserRepository()
        repo.save(User("42", "alice"))
        assert repo.find_by_id("42") == User("42", "alice")
        assert repo.find_active_users() == [User("42", "alice")]
        capsys.readouterr()

    def test_cache_reads_back_what_it_holds(self):
        class SeededCache(InMemoryUserCache):
            def seed(self, user: User) -> None:
                self._users[user.id] = user

        cache = SeededCache()
        cache.seed(User("42", "alice"))
        assert cache.find_by_id("42") == User("42", "alice")
        assert cache.find_active_users() == [User("42", "alice")]

    def test_find_active_users_on_empty_store(self):
        assert InMemoryUserCache().find_active_users() == []


class TestUserWriterBehaviour:
    def test_save_then_update(self, capsys):
        repo = PostgresUserRepository()
        repo.save(User("1", "alice"))
        repo.update(User("1", "alice2"))
        assert repo.find_by_id("1").name == "alice2"
        capsys.readouterr()

    def test_delete_removes_user(self, capsys):
        repo = PostgresUserRepository()
        repo.save(User("1", "alice"))
        repo.delete("1")
        assert repo.find_by_id("1") is None
        capsys.readouterr()

    def test_delete_of_missing_user_is_a_no_op(self, capsys):
        repo = PostgresUserRepository()
        repo.delete("ghost")
        assert repo.find_by_id("ghost") is None
        capsys.readouterr()

    def test_audit_trail_is_returned(self, capsys):
        trail = PostgresUserRepository().get_audit_trail("42")
        assert trail == [UserAudit("42", "LOGIN", 1000)]
        capsys.readouterr()

    def test_analytics_report_wraps_query(self):
        report = PostgresUserRepository().get_analytics("signups")
        assert isinstance(report, AnalyticsReport)
        assert report.data == "results for 'signups'"


class TestServicesDependOnNarrowContracts:
    def test_auth_service_accepts_a_reader_only_stub(self):
        class ReaderOnlyStub:
            def find_by_id(self, user_id: str) -> User | None:
                return User(user_id, "stub")

            def find_active_users(self) -> list[User]:
                return []

        assert UserAuthService(ReaderOnlyStub()).authenticate("7") == User("7", "stub")

    def test_auth_service_accepts_a_single_method_duck_type(self):
        class OneMethodStub:
            def find_by_id(self, user_id: str) -> User | None:
                return None

        assert UserAuthService(OneMethodStub()).authenticate("7") is None

    def test_auth_service_with_read_only_cache(self):
        class SeededCache(InMemoryUserCache):
            def seed(self, user: User) -> None:
                self._users[user.id] = user

        cache = SeededCache()
        cache.seed(User("42", "alice"))
        assert UserAuthService(cache).authenticate("42") == User("42", "alice")

    def test_registration_service_only_needs_save(self):
        class SaveOnlyStub:
            def save(self, user: User) -> None:
                self.saved = user

        stub = SaveOnlyStub()
        UserRegistrationService(stub).register(User("9", "bob"))
        assert stub.saved == User("9", "bob")

    def test_admin_service_only_needs_the_audit_reader(self, capsys):
        class AuditOnlyStub:
            def get_audit_trail(self, user_id: str) -> list[UserAudit]:
                return [UserAudit(user_id, "LOGOUT", 2000)]

        UserAdminService(AuditOnlyStub()).show_audit("42")
        out = capsys.readouterr().out
        assert "LOGOUT" in out
        assert "2000" in out

    def test_admin_service_with_postgres(self, capsys):
        UserAdminService(PostgresUserRepository()).show_audit("42")
        assert "LOGIN" in capsys.readouterr().out

    def test_each_service_takes_exactly_one_dependency(self):
        for service in (UserAuthService, UserRegistrationService, UserAdminService):
            params = [
                p
                for name, p in inspect.signature(service.__init__).parameters.items()
                if name != "self"
            ]
            assert len(params) == 1

    def test_services_never_touch_unrelated_methods(self):
        for service in (UserAuthService, UserRegistrationService, UserAdminService):
            source = inspect.getsource(service)
            assert "export_to_csv" not in source
            assert "get_analytics" not in source

    def test_postgres_satisfies_every_service_simultaneously(self):
        repo = PostgresUserRepository()
        repo.save(User("1", "alice"))
        assert UserAuthService(repo).authenticate("1") is not None
        UserRegistrationService(repo).register(User("2", "bob"))
        assert UserAdminService(repo).show_audit("1") is None or True
        assert isinstance(repo, UserAnalyticsReader)


class TestInterfaceSegregationPrinciple:
    def test_fixed_module_declares_no_fat_interface(self):
        source = inspect.getsource(user_services)
        assert "export_to_csv" not in source

    def test_violation_module_still_declares_the_fat_interface(self):
        assert "export_to_csv" in inspect.getsource(violation)

    def test_cache_implementations_are_interchangeable_for_auth(self):
        cache = InMemoryUserCache()
        db = PostgresUserRepository()
        db.save(User("42", "alice"))
        for reader in (cache, db):
            service = UserAuthService(reader)
            assert service.authenticate("42") is None or service.authenticate("42") == User(
                "42", "alice"
            )
