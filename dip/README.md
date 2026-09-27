# DIP — Dependency Inversion Principle

A ticket-booking use case that depends on **abstractions it owns**, not on
Stripe, Postgres, or Twilio. Swap the vendor, keep the logic; test the logic
with no infrastructure at all.

## Quick Start

```bash
cd dip
python booking_service.py    # run the demo
pytest tests/ -v             # run all tests (25)
```

## The Idea

> High-level modules should not import low-level modules. Both should depend on
> abstractions. Abstractions should not depend on details. Details should depend
> on abstractions.

`BookingService` is high-level policy: *reserve a seat, take payment, notify the
user, and undo the reservation if payment fails*. Stripe and Postgres are
low-level details. In the naive version, `booking_service.py` imports `stripe`
and `psycopg2` and every unit test needs both.

## The Inversion

The three ports are declared **in the domain layer**, next to the use case that
needs them. The adapters import the ports; the ports import nothing.

```
                    booking_service.py  (high level)
        ┌──────────────────────────────────────────────┐
        │  SeatInventoryPort   PaymentPort             │
        │  NotificationPort     BookingService         │
        └───────┬──────────────┬───────────┬──────────┘
                │              │           │
        implements        implements   implements
                │              │           │
   PostgresSeatInventory  Stripe /     Twilio
   FakeSeatInventory      Razorpay     FakeNotification
                          Fake
```

| Port | Declared in | Implemented by |
|------|-------------|----------------|
| `SeatInventoryPort` | `booking_service.py` | `PostgresSeatInventory`, `FakeSeatInventory` |
| `PaymentPort` | `booking_service.py` | `StripePaymentGateway`, `RazorpayPaymentGateway`, `FakePaymentGateway` |
| `NotificationPort` | `booking_service.py` | `TwilioNotificationService`, `FakeNotificationService` |

Nothing in the use case names a vendor. The `PaymentPort` interface happens to
match Stripe's shape, but Stripe does not get to define it.

## The Compensating Transaction

The interesting part of the use case is the rollback:

```python
def book_ticket(self, user_id: str, seat_id: str, price: float) -> bool:
    if not self._inventory.reserve(seat_id, user_id):
        return False                                  # seat gone — stop
    if not self._payment.charge(user_id, price):
        self._inventory.release(seat_id)              # undo the reservation
        return False
    self._notification.send(user_id, f"Booking confirmed for seat {seat_id}")
    return True
```

Because `BookingService` talks to ports, this rollback path is testable with two
three-line fakes. That is the practical payoff of the principle — not
"clean architecture", but *the failure branch is cheap to verify*.

## Test Coverage

`tests/test_dip.py` — 25 tests, 7 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestPortContracts` | All three ports are abstract; adapters implement them; `BookingService` source names no vendor |
| `TestHappyPath` | Returns `True`, notifies with the seat reference, does not release, prints success, zero-price booking works |
| `TestReservationFailure` | Returns `False`, payment is never attempted (exploding payment double), no notification, failure is reported |
| `TestPaymentFailure` | Returns `False`, releases the seat, no notification, failure is reported |
| `TestDependencyInversion` | Stripe→Razorpay swap needs no service change; constructor signature is vendor-free; a brand-new `PayPalGateway` works with no registration; production adapters print the expected lines; fakes cover the demo's assertions |

`TestReservationFailure::test_payment_is_not_attempted` installs a payment port
that raises on `charge`. If the ordering in `book_ticket` ever regresses, the
suite fails instead of silently double-charging.

## Run It

```
[Postgres] Reserved seat=A12 user=user-42
[Stripe] Charged 250.0 for user-42
[Twilio] SMS to user-42: Booking confirmed for seat A12
[Booking] Success: A12

Swap Stripe -> Razorpay; BookingService untouched:
[Postgres] Reserved seat=B7 user=user-42
[Razorpay] Charged 250.0 for user-42
[Booking] Success: B7

Unit-test booking logic with fakes (payment declines):
[Booking] Payment failed, released seat
[Test] Seat released after failed payment, no notification sent
```

## Structure

```
dip/
├── booking_service.py   # 3 ports, BookingService, 3 real adapters, 3 fakes, main()
├── tests/
│   └── test_dip.py      # 25 tests
└── README.md
```

## Conventions

- Python 3.10+ type hints
- Ports named `<Domain>Port`, adapters named `<Vendor><Role>`
- `pytest` for testing
