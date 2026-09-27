# LSP — Liskov Substitution Principle

Two files, side by side: the **violation** and the **fix**. A generic garage
service that works for every vehicle — including a scooter that cannot refuel.

## Quick Start

```bash
cd lsp
python violation.py           # watch the anti-pattern crash
python garage_service.py      # watch the fix work
pytest tests/ -v             # run all tests (19)
```

## The Idea

> If a subclass can be substituted for its base class without changing the
> correctness of the program, the subclass is substitutable.

`GarageService.service(vehicle: Vehicle)` is a function that promises *"any
vehicle can be serviced"*. With a single fat `Vehicle` interface, that promise is
a lie for anything that is not petrol.

## The Violation — `violation.py`

```python
class Vehicle(ABC):
    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def refuel(self) -> None: ...

class ElectricScooter(Vehicle):
    def start(self) -> None:
        print("[Scooter] Motor engaged silently")

    def refuel(self) -> None:
        raise NotImplementedError("Scooters don't refuel")

def service(vehicle: Vehicle) -> None:
    vehicle.start()
    vehicle.refuel()        # type-checks fine, blows up at runtime
    print("Service complete")
```

The subtype satisfies the *signature* but breaks the *contract*. Static
analysers, type checkers, and reviewers all pass it. The failure only appears
in production:

```
Starting service...
[Scooter] Motor engaged silently
[Main] Crashed while servicing scooter: Scooters don't refuel
```

Note the missing `Service complete` — the program is left half-done, which is
worse than a clean rejection.

## The Fix — `garage_service.py`

Split the fat interface into one interface per capability, so the type system
only ever demands what a thing can actually do.

```
Startable          Refuelable         Rechargeable
    │                    │                   │
    ├── PetrolCar ───────┤                   │
    │                    │                   │
    └── ElectricScooter ─┴───────────────────┤
                          (not Refuelable)  │
```

```python
def service(vehicle: Startable) -> None:
    vehicle.start()
    if isinstance(vehicle, Refuelable):
        vehicle.refuel()
    elif isinstance(vehicle, Rechargeable):
        vehicle.charge()
```

| | Violation | Fix |
|---|-----------|-----|
| Interfaces | 1 (`Vehicle`, 2 methods) | 3 (`Startable`, `Refuelable`, `Rechargeable`) |
| Scooter `refuel` | raises `NotImplementedError` | method does not exist |
| Service parameter | `Vehicle` | `Startable` |
| New capability | edit `Vehicle` + every subclass + the service | add a new ABC, one `isinstance` branch |
| Failure mode | runtime crash mid-transaction | compile-time absence of the method |

The scooter is now substitutable everywhere a `Startable` is expected, and
cannot be passed where a `Refuelable` is expected — which is exactly right.

A vehicle that is both `Refuelable` and `Rechargeable` (a hybrid) is refuelled,
because the `if` branch wins. That precedence is pinned down by a test.

## Test Coverage

`tests/test_lsp.py` — 19 tests, 5 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestViolation` | `Vehicle` is abstract; scooter `refuel` raises; the scooter still passes `isinstance(Vehicle)`; the generic service crashes and never reaches `Service complete`, while a petrol vehicle completes normally |
| `TestCapabilityInterfaces` | `Refuelable` and `Rechargeable` are unrelated; each vehicle satisfies exactly the capabilities it should |
| `TestGarageService` | Petrol path, electric path, `Startable`-only vehicle, hybrid precedence, no substitution ever raises |
| `TestSubstitutability` | Mixed list of vehicles through one `Startable`-typed reference; no `NotImplementedError` stubs remain in the fixed module |
| `TestFixedAndViolatingScootersBehaveTheSame` | The fix preserves the original `start()` behaviour |

## Structure

```
lsp/
├── violation.py          # fat Vehicle interface — the anti-pattern
├── garage_service.py     # capability interfaces — the fix
├── tests/
│   └── test_lsp.py       # 19 tests
└── README.md
```

> Both modules define a class named `ElectricScooter`. Tests import them under
> aliases (`from violation import ElectricScooter as ViolationScooter`).

## Conventions

- Python 3.10+
- One ABC per capability, named for the capability not the thing
- `pytest` for testing
