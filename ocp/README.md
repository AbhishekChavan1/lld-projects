# OCP — Open/Closed Principle

A payment router that is **open for extension, closed for modification**. New
payment methods are added by writing a new class and registering it — the router
is never edited.

## Quick Start

```bash
cd ocp
python payment_router.py     # run the demo
pytest tests/ -v             # run all tests (22)
```

## The Idea

The closed version of a payment router looks like this:

```python
def process(self, payment_type, amount):
    if payment_type == "CARD":
        ...
    elif payment_type == "UPI":
        ...
    elif payment_type == "CRYPTO":     # every new method edits this function
        ...
```

Every new provider modifies a class that already works, already has tests, and
is already deployed. The open version inverts it: handlers register themselves
under a key, and the router only ever looks handlers up.

```
PaymentRouter                    <- never mentions a payment method
  _handlers: dict[str, PaymentHandler]
  register(type, handler)   ──┐
  get_handler(type)        ──┤
                             │
   ┌─────────────┬───────────┼───────────┬──────────────────┐
   │             │           │           │                  │
CardPayment  UPIPayment  WalletPayment  NetBanking     CryptoPayment
                                              │
                                 (added in net_banking.py,
                                  zero edits to payment_router.py)
```

## Extending It

Adding a provider is two steps and touches no existing file:

```python
# net_banking.py
from payment_router import PaymentHandler

class NetBankingPaymentHandler(PaymentHandler):
    def process(self, amount: float) -> None:
        status = "Redirect to bank portal" if amount > 10000 else "Direct debit"
        print(f"[NetBanking] Processing {amount} via net banking. {status}")
```

```python
router.register("NETBANKING", NetBankingPaymentHandler())
```

## Handlers

| Handler | File | Rule demonstrated |
|---------|------|-------------------|
| `CardPaymentHandler` | `payment_router.py` | 3DS above $100 |
| `UPIPaymentHandler` | `payment_router.py` | OTP above $5000 |
| `WalletPaymentHandler` | `payment_router.py` | balance check at $500 |
| `NetBankingPaymentHandler` | `net_banking.py` | portal redirect above $10000 |

Per-handler thresholds are the point: each provider keeps its own quirky rules
instead of leaking them into a shared `if` ladder.

## Test Coverage

`tests/test_ocp.py` — 22 tests, 5 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestPaymentHandlerContract` | `PaymentHandler` is abstract; every handler implements only `process` |
| `TestRouterRegistration` | Empty by default, case-insensitive lookup, unknown type raises, re-registration replaces |
| `TestHandlerBehaviour` | Each handler's threshold, boundary values (100, 5000, 500, 10000), router dispatch |
| `TestOpenClosedPrinciple` | A brand-new handler registers and works; `PaymentRouter` source names no payment method and uses no `isinstance`; router exposes only `register`/`get_handler` |

The `TestOpenClosedPrinciple` group is the real OCP check: it defines a
`CryptoPaymentHandler` inside the test file and proves it works without any
production change. It also asserts the router's source contains no concrete
payment-method name, so a regression to a branching router fails the suite.

## Run It

```
Payment via CARD:
[Card] Processing 250.0 via card gateway. Auth: 3DS required
Payment via UPI:
[UPI] Processing 250.0 via UPI. Quick pay
Payment via WALLET:
[Wallet] Processing 250.0 via wallet. Balance check: Low balance fallback
[Main] Error: Unknown payment type: NETBANKING
Payment via NETBANKING (added with zero existing-code changes):
[NetBanking] Processing 250.0 via net banking. Direct debit
```

## Structure

```
ocp/
├── payment_router.py    # PaymentHandler ABC, 3 handlers, PaymentRouter, main()
├── net_banking.py       # NetBankingPaymentHandler — the extension, added later
├── tests/
│   └── test_ocp.py      # 22 tests
└── README.md
```

## Conventions

- Python 3.10+
- Handlers are stateless; the router owns the registry
- `pytest` for testing
