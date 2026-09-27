# LLD Projects

A collection of Low-Level Design (LLD) mini-projects in Python, each demonstrating design patterns, OOP principles, and clean architecture.

## Projects

| Project | Description | Design Patterns | Tests |
|---------|-------------|-----------------|-------|
| [atm](atm/) | ATM machine simulation with card/PIN auth, withdrawals, deposits | State Pattern, Composition | Yes (10) |
| [awslocker](awslocker/) | Amazon Hub Locker assignment and pickup system | Dataclass Modeling, Service Layer | Yes (8) |
| [ratelimiter](ratelimiter/) | Thread-safe rate-limiting library with multiple algorithms | Strategy Pattern, ABC | Yes (14) |
| [ridesharing](ridesharing/) | Ride-hailing system with pluggable matching and pricing | Strategy Pattern, State Machine, Decorator | Yes (16) |
| [snake_ladder](snake_ladder/) | Snake & ladder with pluggable dice and validated board | Strategy Pattern, FIFO Turn Queue | Yes (27) |
| [oop-examples](oop-examples/) | OOP principle demos: encapsulation, abstraction, composition | ABC, DI, Name Mangling | Yes (116) |
| [library-oop](library-oop/) | Library management system (OOP exercise) | Inheritance, Composition, Strategy Pattern | Yes (14) |
| [parkinglot](parkinglot/) | Multi-floor parking lot with pluggable pricing and payments | Strategy Pattern, Factory Pattern, Composition | Yes (20) |
| [design-patterns](design-patterns/) | Creational patterns: Singleton, Prototype, Object Pool, Factory | Singleton, Prototype, Object Pool, Factory | Yes (52) |
| [design-patterns-structural](design-patterns-structural/) | Third-party payment/notification SDKs behind own interfaces | Adapter (Object & Class), Ports & Adapters | Yes (169) |
| [vending machine](vending%20machine/) | Vending machine with greedy change and refund-on-failure | State Pattern, Greedy Algorithm, Locking | Yes (45) |
| [coffee-machine](coffee-machine/) | Configurable beverage machine with ingredient tracking | Decorator Pattern, State Pattern, RLock | Yes (51) |
| [srp](srp/) | Order placement split into single-responsibility collaborators | SRP, Strategy Pattern, DI | Yes (35) |
| [ocp](ocp/) | Payment router extended without modification | OCP, Registry, Strategy Pattern | Yes (22) |
| [lsp](lsp/) | Garage service — violation and capability-interface fix | Liskov Substitution, Interface Segregation | Yes (19) |
| [isp](isp/) | User services — fat repository violation and narrow-role fix | Interface Segregation, DI | Yes (37) |
| [dip](dip/) | Ticket booking with swappable vendor adapters and fakes | Dependency Inversion, Ports & Adapters | Yes (25) |

## Quick Start

Each project is self-contained. Navigate into any project and run it:

```bash
cd atm
python main.py        # run the demo
pytest tests/         # run tests
```

Tests are run from **inside** a project directory, not from the repo root — most
projects use top-level imports (`from models.coin import Coin`) rather than
package-relative ones.

## Structure

```
lld-projects/
├── atm/                 # State pattern
├── awslocker/           # Dataclasses + service layer
├── coffee-machine/      # Decorator + State
├── design-patterns/     # Creational patterns
├── design-patterns-structural/  # Structural patterns (Adapter)
├── dip/                 # SOLID: dependency inversion
├── isp/                 # SOLID: interface segregation
├── library-oop/         # Encapsulation + composition
├── lsp/                 # SOLID: liskov substitution
├── ocp/                 # SOLID: open/closed
├── oop-examples/        # Encapsulation, abstraction, composition
├── parkinglot/          # Strategy + Factory
├── ratelimiter/         # Strategy + ABC
├── ridesharing/         # Strategy + State + Decorator
├── snake_ladder/        # Strategy + validated board
├── srp/                 # SOLID: single responsibility
├── vending machine/     # State pattern (folder name contains a space)
└── README.md
```

## Conventions

- Python 3.10+
- Type hints where practical
- `pytest` for testing
- snake_case for files and functions
- PascalCase for classes
- Each project has its own `README.md` with details

## Status

All 17 projects ship with tests: **680 passing, 0 failing**.
