# LLD Projects

A collection of Low-Level Design (LLD) mini-projects in Python, each demonstrating design patterns, OOP principles, and clean architecture.

## Projects

| Project | Description | Design Patterns | Tests |
|---------|-------------|-----------------|-------|
| [atm](atm/) | ATM machine simulation with card/PIN auth, withdrawals, deposits | State Pattern, Composition | Yes |
| [awslocker](awslocker/) | Amazon Hub Locker assignment and pickup system | Dataclass Modeling, Service Layer | Yes |
| [ratelimiter](ratelimiter/) | Thread-safe rate-limiting library with multiple algorithms | Strategy Pattern, ABC | Yes |
| [ridesharing](ridesharing/) | Ride-hailing system with pluggable matching and pricing | Strategy Pattern, State Machine, Decorator | Yes |
| [oop-examples](oop-examples/) | OOP principle demos: encapsulation, abstraction, composition | ABC, DI, Name Mangling | Yes |
| [library-oop](library-oop/) | Library management system (OOP exercise) | Inheritance, Composition, Strategy Pattern | Yes |
| [parkinglot](parkinglot/) | Multi-floor parking lot with pluggable pricing and payments | Strategy Pattern, Factory Pattern, Composition | Yes |
| [design-patterns](design-patterns/) | Creational patterns: Singleton, Prototype, Object Pool, Factory | Singleton, Prototype, Object Pool, Factory | Yes (52) |
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
