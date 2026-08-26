# Design Patterns - Creational Patterns (LLD)

Production-ready Python implementations of **Singleton, Prototype, Object Pool & Factory** creational design patterns, following the LLD interview patterns from [The Design Round](https://thedesignround.com/machine-coding/design-patterns).

## Quick Start

```bash
cd design-patterns
python main.py        # run the demo
pytest tests/ -v      # run all tests
```

## Patterns Overview

| Pattern | Problem Solved | LLD Use Cases |
|---------|---------------|---------------|
| **Singleton** | Ensure one instance, global access | DB pools, Logger, Config |
| **Prototype** | Clone expensive objects cheaply | Cache, Document templates, RBAC |
| **Object Pool** | Reuse expensive resources | Connection pools, Thread pools |
| **Factory** | Centralize object creation | Parking spots, Notification channels |

---

## Singleton Pattern

**Ensures a class has exactly ONE instance and provides a global point of access.**

| Class | Flavor | Use Case |
|-------|--------|----------|
| `DatabaseConnection` | Metaclass | Central DB pool shared across entry gates |
| `Logger` | `__new__` | Single log queue to prevent interleaved output |
| `AppConfig` | `__new__` | Config loaded once from env/files |

---

## Prototype Pattern

**Creates copies of objects cheaply by cloning existing instances instead of rebuilding from scratch.**

| Class | What it Clones | Use Case |
|-------|---------------|----------|
| `ReportDocument` | Documents with sections/metadata | Cache responses, document templates |
| `AdminUser` / `RegularUser` | User permission templates | Auth registries, RBAC |
| `UserPrototypeRegistry` | Registry of clonable templates | Central factory for role-based users |

---

## Object Pool Pattern

**Maintains a pool of reusable objects (DB connections, threads) instead of creating/destroying per request.**

| Class | What it Pools | Use Case |
|-------|--------------|----------|
| `ConnectionPool` | DB connections with pre-warming | Parking Lot gates, API servers |
| `WorkerPool` | Worker threads with task queue | Job Scheduler, Notification Service |

---

## Factory Pattern

**Centralizes object creation logic, eliminating scattered if/else chains.**

| Factory | Product | Pattern Type |
|---------|---------|-------------|
| `ParkingSpotFactory` | `CarSpot`, `BikeSpot`, `TruckSpot` | Simple Factory (registry) |
| `NotificationChannelFactory` | `EmailChannel`, `SMSChannel`, `PushChannel` | Factory Method |
| `EmailCreator`, `SMSCreator` | Channel subclass creators | Factory Method (subclass) |

---

## Structure

```
design-patterns/
├── singleton/
│   ├── metaclass_singleton.py    # DatabaseConnection
│   ├── logger_singleton.py       # Logger
│   └── config_singleton.py       # AppConfig
├── prototype/
│   ├── document_prototype.py     # ReportDocument
│   └── user_prototype.py         # AdminUser, RegularUser, Registry
├── object_pool/
│   ├── connection_pool.py        # ConnectionPool
│   └── worker_pool.py            # WorkerPool
├── factory/
│   ├── parking_spot_factory.py   # ParkingSpotFactory (Simple Factory)
│   └── notification_factory.py   # NotificationChannelFactory (Factory Method)
├── tests/                        # 52 tests
├── main.py
└── README.md
```

## Conventions

- Python 3.10+
- Type hints everywhere
- `pytest` for testing
- snake_case for files, PascalCase for classes
- Each singleton has a `reset()` / `clear_instance()` for testability
