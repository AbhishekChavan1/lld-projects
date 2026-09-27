# SRP — Single Responsibility Principle

Order placement split so that **every class has exactly one reason to change**.
Validation, pricing, persistence, and notification are four independent
collaborators injected into a thin application service.

## Quick Start

```bash
cd srp
python order_processing.py   # run the demo
pytest tests/ -v             # run all tests (35)
```

## The Idea

A class has one responsibility if there is **one axis of change** that affects it.
A change to coupon rules should never touch the validator; swapping the database
should never touch the notifier.

```
OrderApplicationService          <- orchestrates, contains no rules
  ├── OrderValidator             <- "is this order legal?"
  ├── PricingService (ABC)       <- "what does it cost?"
  │     └── CouponPricingService
  ├── OrderRepository (ABC)      <- "where is it stored?"
  │     └── InMemoryOrderRepository
  └── NotificationService (ABC)  <- "tell the user"
        └── EmailNotificationService
```

`place_order` is a four-step pipeline with zero branching:

```python
def place_order(self, order: Order) -> float:
    self._validator.validate(order)                      # 1. reject bad input
    final_amount = self._pricing_service.apply_discount(order)  # 2. price it
    self._repository.save(order)                        # 3. persist it
    self._notification_service.send_confirmation(...)   # 4. inform the user
    return final_amount
```

`Order` is a frozen dataclass, so it is pure data with no behaviour to hide.

## Why It Is SRP

| Class | Single reason to change |
|-------|-------------------------|
| `OrderValidator` | validation rules change |
| `CouponPricingService` | discount policy changes |
| `InMemoryOrderRepository` | storage mechanism changes |
| `EmailNotificationService` | notification channel changes |
| `OrderApplicationService` | the *order of the steps* changes |

The application service contains no `if`/`elif` and no vendor names, so adding a
payment provider, a new discount, or a SQL repository requires zero edits here.

## Test Coverage

`tests/test_srp.py` — 35 tests, 8 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestOrder` | Field defaults, frozen immutability, value equality, hashability |
| `TestOrderValidator` | Zero/negative amount, empty and whitespace user IDs, check ordering |
| `TestPricingService` | ABC is abstract, 10% coupon, unknown/absent coupon, cent rounding |
| `TestInMemoryOrderRepository` | ABC is abstract, save/get round trip, missing key, overwrite by id |
| `TestEmailNotificationService` | ABC is abstract, confirmation output |
| `TestOrderApplicationService` | Returned amount, persistence, notification, invalid order not persisted and not notified, validation runs before pricing, exact step ordering via spies |
| `TestSingleResponsibility` | Each collaborator exposes one public method; the service exposes only `place_order`; `place_order` source contains no branches or vendor names; strategies are swappable |

Structural assertions (public-method counts, source inspection) are used
deliberately: SRP is a property of a class's *shape*, so it is verified by
inspecting shape, not only behaviour.

## Run It

```
[Main] Order placed. Final amount: 225.0
[Notification] Confirmation sent to user user-42 for order ORD-001
[Main] Rejected invalid order: Amount must be positive
```

## Structure

```
srp/
├── order_processing.py       # Order, 4 ABCs, 3 impls, application service, main()
├── tests/
│   └── test_srp.py           # 35 tests
└── README.md
```

## Conventions

- Python 3.10+ (`X | None` unions)
- `@dataclass(frozen=True)` for value objects
- `pytest` for testing
