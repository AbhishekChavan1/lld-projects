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


class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    def save(self, user: User) -> None:
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        pass

    @abstractmethod
    def update(self, user: User) -> None:
        pass

    @abstractmethod
    def find_active_users(self) -> list[User]:
        pass

    @abstractmethod
    def get_audit_trail(self, user_id: str) -> list[UserAudit]:
        pass

    @abstractmethod
    def get_analytics(self, query: str) -> AnalyticsReport:
        pass

    @abstractmethod
    def export_to_csv(self) -> None:
        pass


class InMemoryUserCache(UserRepository):
    """Only wants read access but is forced to implement the whole fat interface."""

    def __init__(self):
        self._users: dict[str, User] = {}

    def find_by_id(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def delete(self, user_id: str) -> None:
        self._users.pop(user_id, None)

    def update(self, user: User) -> None:
        self._users[user.id] = user

    def find_active_users(self) -> list[User]:
        return list(self._users.values())

    def get_audit_trail(self, user_id: str) -> list[UserAudit]:
        raise NotImplementedError("Cache has no audit trail")

    def get_analytics(self, query: str) -> AnalyticsReport:
        raise NotImplementedError("Cache has no analytics")

    def export_to_csv(self) -> None:
        raise NotImplementedError("Cache cannot export")


class UserAuthService:
    """Depends on the fat interface even though it needs one method."""

    def __init__(self, repository: UserRepository):
        self._repository = repository

    def authenticate(self, user_id: str) -> User | None:
        return self._repository.find_by_id(user_id)


def main():
    cache = InMemoryUserCache()
    cache.save(User("42", "alice"))

    auth = UserAuthService(cache)
    user = auth.authenticate("42")
    print(f"[Auth] Authenticated: {user}")

    try:
        cache.get_audit_trail("42")
    except NotImplementedError as e:
        print(f"[Main] Fat interface strikes again: {e}")


if __name__ == "__main__":
    main()
