# ISP — Interface Segregation Principle

Two files, side by side: the **violation** (one fat repository interface) and
the **fix** (four narrow role interfaces). A read-only cache is the test case —
it should not be forced to pretend it can export CSV.

## Quick Start

```bash
cd isp
python violation.py         # watch the fat interface force dead code
python user_services.py     # watch the segregated version
pytest tests/ -v           # run all tests (37)
```

## The Idea

> Clients should not be forced to depend on methods they do not use.

A dependency on a wide interface is a dependency on code you will never run,
cannot test meaningfully, and will break when someone else needs it changed.

## The Violation — `violation.py`

One `UserRepository` with **8** abstract methods. An `InMemoryUserCache` only
wants reads, so it implements all 8 anyway:

```python
class InMemoryUserCache(UserRepository):
    def get_audit_trail(self, user_id): raise NotImplementedError("Cache has no audit trail")
    def get_analytics(self, query):    raise NotImplementedError("Cache has no analytics")
    def export_to_csv(self):           raise NotImplementedError("Cache cannot export")
    # ...plus find_by_id, save, delete, update, find_active_users it never needed
```

Three of those methods are lie detectors. `isinstance(cache, UserRepository)`
returns `True`, every type checker approves, and the `NotImplementedError`
surfaces as a production incident:

```
[Auth] Authenticated: User(id='42', name='alice')
[Main] Fat interface strikes again: Cache has no audit trail
```

The client is guilty too — `UserAuthService` needs exactly one method but
declares a dependency on all eight.

## The Fix — `user_services.py`

Split by role. Each client depends only on what it calls.

| Interface | Methods | Implemented by |
|-----------|---------|----------------|
| `UserReader` | `find_by_id`, `find_active_users` | `PostgresUserRepository`, `InMemoryUserCache` |
| `UserWriter` | `save`, `update`, `delete` | `PostgresUserRepository` |
| `UserAuditReader` | `get_audit_trail` | `PostgresUserRepository` |
| `UserAnalyticsReader` | `get_analytics` | `PostgresUserRepository` |

| Service | Depends on | Calls |
|---------|-----------|-------|
| `UserAuthService` | `UserReader` | `find_by_id` |
| `UserRegistrationService` | `UserWriter` | `save` |
| `UserAdminService` | `UserAuditReader` | `get_audit_trail` |

The fixed `InMemoryUserCache` implements **2** methods, has zero dead code, and
cannot be handed to a service that needs writes. `PostgresUserRepository`
implements all four, so it still satisfies every service at once.

```
[Auth] Authenticated: None
[DB] INSERT INTO users ...
[Admin] Audit: UserAudit(user_id='42', action='LOGIN', timestamp=1000)
[Auth] Cache lookup: None
```

## Test Coverage

`tests/test_isp.py` — 37 tests, 7 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestViolation` | Fat interface has 8 methods; unsupported members raise at runtime; `isinstance` still lies; the service takes the fat dependency |
| `TestNarrowInterfaces` | All four ABCs are abstract; each is 1–3 methods; no interface claims another's responsibility; `InMemoryUserCache` is *only* a `UserReader` and contains no `NotImplementedError` |
| `TestUserReaderImplementations` | Missing user returns `None` on both stores; save/read round trips on the DB; read-only cache reads back what it holds |
| `TestUserWriterBehaviour` | Save/update/delete, delete of a missing user, audit trail, analytics report |
| `TestServicesDependOnNarrowContracts` | Auth service accepts a reader-only stub *and* a bare one-method duck type; registration service needs only `save`; admin service needs only `get_audit_trail`; each service takes exactly one dependency; no service source mentions `export_to_csv` or `get_analytics` |
| `TestInterfaceSegregationPrinciple` | The fixed module declares no `export_to_csv`; the violation module still does; readers are interchangeable for auth |

The service tests deliberately pass hand-written stubs with a single method.
That is the practical payoff of ISP: `UserAuthService` can be unit tested without
implementing a repository.

> Both modules define `User`, `UserAudit`, `AnalyticsReport`,
> `InMemoryUserCache`, and `UserAuthService`. Tests import them under aliases
> (`from violation import User as FatUser`, etc.).

## Structure

```
isp/
├── violation.py        # fat 8-method UserRepository — the anti-pattern
├── user_services.py    # 4 narrow interfaces — the fix
├── tests/
│   └── test_isp.py     # 37 tests
└── README.md
```

## Conventions

- Python 3.10+ (`X | None` unions)
- Interfaces named `<Role><Verb>` (`UserReader`, `UserAuditReader`)
- `pytest` for testing
