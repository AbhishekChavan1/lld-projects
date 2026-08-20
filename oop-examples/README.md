# OOP Examples

Demonstrations of core OOP principles in Python through practical, runnable examples.

## Principles Covered

| Example | Principle | Key Concepts |
|---------|-----------|--------------|
| [encapsulation](encapsulation/car_engine.py) | Encapsulation | Name mangling (`__private`), state management, component composition |
| [abstraction](abstraction/accounts.py) | Abstraction | ABC, abstract methods, concrete implementations with domain rules |
| [composition](composition/employee.py) | Composition | Dependency injection, interface segregation, multiple inheritance |

## Quick Start

```bash
cd projects/oop-examples

python encapsulation/car_engine.py
python abstraction/accounts.py
python composition/employee.py
```

## Structure

```
oop-examples/
├── __init__.py
├── abstraction/
│   ├── __init__.py
│   └── accounts.py          # Account hierarchy: Savings, Current, FixedDeposit
├── composition/
│   ├── __init__.py
│   └── employee.py           # Employee/Manager/Contractor with DI
├── encapsulation/
│   ├── __init__.py
│   └── car_engine.py         # Car + Engine + Wheel with name mangling
└── README.md
```
