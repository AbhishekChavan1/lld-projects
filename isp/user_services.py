from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: str
    name: str


@dataclass(frozen=True)
class UserAudit:
    user_id: str
    action: str
    timestamp: int


class AnalyticsReport:
    def __init__(self, data: str):
        self.data = data


class UserReader(ABC):
    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    def find_active_users(self) -> list[User]:
        pass


class UserWriter(ABC):
    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def update(self, user: User) -> None:
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        pass


class UserAuditReader(ABC):
    @abstractmethod
    def get_audit_trail(self, user_id: str) -> list[UserAudit]:
        pass


class UserAnalyticsReader(ABC):
    @abstractmethod
    def get_analytics(self, query: str) -> AnalyticsReport:
        pass


class PostgresUserRepository(UserReader, UserWriter, UserAuditReader, UserAnalyticsReader):
    def __init__(self):
        self._users: dict[str, User] = {}

    def find_by_id(self, user_id: str) -> User | None:
        print(f"[DB] SELECT * FROM users WHERE id = {user_id}")
        return self._users.get(user_id)

    def find_active_users(self) -> list[User]:
        return list(self._users.values())

    def save(self, user: User) -> None:
        print("[DB] INSERT INTO users ...")
        self._users[user.id] = user

    def update(self, user: User) -> None:
        print("[DB] UPDATE users ...")
        self._users[user.id] = user

    def delete(self, user_id: str) -> None:
        print("[DB] DELETE FROM users ...")
        self._users.pop(user_id, None)

    def get_audit_trail(self, user_id: str) -> list[UserAudit]:
        return [UserAudit(user_id, "LOGIN", 1000)]

    def get_analytics(self, query: str) -> AnalyticsReport:
        return AnalyticsReport(f"results for '{query}'")


class InMemoryUserCache(UserReader):
    """Implements only the contract it can actually satisfy."""

    def __init__(self):
        self._users: dict[str, User] = {}

    def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def find_active_users(self) -> list[User]:
        return list(self._users.values())


class UserAuthService:
    def __init__(self, reader: UserReader):
        self._reader = reader

    def authenticate(self, user_id: str) -> User | None:
        return self._reader.find_by_id(user_id)


class UserRegistrationService:
    def __init__(self, writer: UserWriter):
        self._writer = writer

    def register(self, user: User) -> None:
        self._writer.save(user)


class UserAdminService:
    def __init__(self, audit_reader: UserAuditReader):
        self._audit_reader = audit_reader

    def show_audit(self, user_id: str) -> None:
        for entry in self._audit_reader.get_audit_trail(user_id):
            print(f"[Admin] Audit: {entry}")


def main():
    repo = PostgresUserRepository()

    auth = UserAuthService(repo)
    print(f"[Auth] Authenticated: {auth.authenticate('42')}")

    reg = UserRegistrationService(repo)
    reg.register(User("99", "bob"))

    admin = UserAdminService(repo)
    admin.show_audit("42")

    cache = InMemoryUserCache()
    cache_service = UserAuthService(cache)
    print(f"[Auth] Cache lookup: {cache_service.authenticate('42')}")


if __name__ == "__main__":
    main()
