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
| [library-oop](library-oop/) | Library management system (OOP exercise) | Inheritance, Composition | Yes |
| [parkinglot](parkinglot/) | Multi-floor parking lot with pluggable pricing and payments | Strategy Pattern, Factory Pattern, Composition | Yes |
| [design-patterns](design-patterns/) | Singleton & Prototype pattern implementations with LLD examples | Singleton, Prototype | Yes |

## Quick Start

Each project is self-contained. Navigate into any project and run it:

```bash
cd atm
python main.py        # run the demo
pytest tests/         # run tests
```

## Structure

```
lld-projects/
├── atm/
├── awslocker/
├── library-oop/
├── oop-examples/
├── parkinglot/
├── ratelimiter/
├── ridesharing/
├── design-patterns/
└── README.md
```

## Conventions

- Python 3.10+
- Type hints where practical
- `pytest` for testing
- snake_case for files and functions
- PascalCase for classes
- Each project has its own `README.md` with details
