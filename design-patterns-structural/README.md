# Design Patterns - Structural Patterns (LLD)

Production-ready Python implementations of the **Structural** Gang of Four
patterns, following the LLD interview patterns from
[The Design Round](https://thedesignround.com/machine-coding/design-patterns).

## Quick Start

```bash
cd design-patterns-structural
python main.py        # run the demo
pytest tests/ -v      # run all tests
```

## Patterns Overview

| Pattern | Problem Solved | LLD Use Cases |
|---------|---------------|---------------|
| **Adapter** | Bridge two incompatible interfaces | Third-party payment/notification SDKs |

## Adapter

A vendor's SDK has an awkward shape — integer minor units, untyped dicts, a
mandatory auth handshake, failures returned as codes instead of raised. The
Adapter puts *your* interface in front of it so none of that reaches your
business logic.

| File | Role |
|------|------|
| `adapter/ports.py` | `PaymentGateway` / `NotificationSender` — the interfaces the app owns |
| `adapter/status_translation.py` | Vendor state codes → `PaymentStatus` |
| `adapter/legacy_paypal_sdk.py` | Adaptee: cents, dict results, mandatory auth, error codes |
| `adapter/acquirer_sdk.py` | Adaptee: minor units, exceptions, partial refunds |
| `adapter/notification_sdks.py` | Adaptors: SMS dict status vs. SMTP integer errno |
| `adapter/payment_adapters.py` | Object adapters + `InHouseLedgerGateway` (first-party, not an adapter) |
| `adapter/class_adapter.py` | Inheritance-based adapter, kept for contrast |
| `adapter/leaky_client.py` | The "before" picture — same logic, every vendor quirk leaking |
| `adapter/registry.py` | `GatewayRegistry` + vendor-agnostic `CheckoutService` |

### Object vs. Class Adapter

| | Object (composition) | Class (inheritance) |
|---|---|---|
| Holds the adaptee | in a field | as a base class |
| Adaptee methods reachable? | no | **yes** — the leak |
| Use when | you have an instance to wrap | you cannot get an instance |

Both satisfy `PaymentGateway` identically. The class adapter also exposes
`charge_cents()`, so a client can bypass the target interface. The test suite
asserts that asymmetry.

## Structure

```
design-patterns-structural/
├── adapter/
│   ├── __init__.py
│   ├── ports.py                  # PaymentGateway, NotificationSender (target)
│   ├── status_translation.py     # vendor state codes -> PaymentStatus
│   ├── legacy_paypal_sdk.py      # adaptee
│   ├── acquirer_sdk.py           # adaptee
│   ├── notification_sdks.py      # adaptors
│   ├── payment_adapters.py       # object adapters
│   ├── class_adapter.py          # class adapter
│   ├── leaky_client.py           # no-adapter anti-pattern
│   └── registry.py               # registry + CheckoutService
├── tests/                        # 169 tests
├── main.py
└── README.md
```

## What the Tests Cover

| Area | What is asserted |
|------|------------------|
| Adaptees | each SDK's own quirks: auth handshake, risk limit, tier limit, errno codes, segment cap |
| Adapters | unit conversion, lazy auth, dict → `PaymentResult`, both error conventions → one enum |
| Boundary cases | risk-limit and tier-limit edges, zero/negative/sub-minor amounts, bad numbers, bad emails |
| Isolation | `PayPalAdapter` exposes only `charge`/`refund`/`get_provider_name`; `charge_cents` is unreachable |
| Class adapter | satisfies the same interface, but `charge_cents` *is* reachable — the leak the object adapter prevents |
| Architecture | `inspect.getsource` asserts the target interfaces and `CheckoutService` name no vendor detail |
| Registry / service | one `CheckoutService` works against every registered provider, unchanged |

## Conventions

- Python 3.10+
- Type hints everywhere, `from __future__ import annotations`
- `pytest` for testing
- snake_case for files and functions, PascalCase for classes
- Vendor SDKs are simulated in-repo so the demo needs no credentials
