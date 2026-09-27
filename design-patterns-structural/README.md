# Design Patterns - Structural Patterns (LLD)

Production-ready Python implementations of the **Structural** Gang of Four
patterns, following the LLD interview patterns from
[The Design Round](https://thedesignround.com/machine-coding/design-patterns).

## Quick Start

```bash
cd design-patterns-structural
python main.py            # every pattern
python main.py bridge     # one pattern
pytest tests/ -v          # run all tests
```

## Patterns Overview

| Pattern | Problem Solved | LLD Use Cases |
|---------|---------------|---------------|
| **Adapter** | Bridge two incompatible interfaces | Third-party payment/notification SDKs |
| **Bridge** | Decouple two axes that vary independently | message × channel, shape × renderer |

---

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
| `adapter/demo.py` | All six Adapter demos, runnable as `python -m adapter.demo` |

Vendor payloads are typed with `TypedDict` (`PayPalCharge`, `AcquirerPayment`,
`SmsResponse`, `CheckoutOutcome`, `RefundOutcome`), so a caller reads
`outcome["status"]` as a real `str` rather than `Any`.

### Object vs. Class Adapter

| | Object (composition) | Class (inheritance) |
|---|---|---|
| Holds the adaptee | in a field | as a base class |
| Adaptee methods reachable? | no | **yes** — the leak |
| Use when | you have an instance to wrap | you cannot get an instance |

Both satisfy `PaymentGateway` identically. The class adapter also exposes
`charge_cents()`, so a client can bypass the target interface. The test suite
asserts that asymmetry.

---

## Bridge

Two axes that grow independently. A Bridge is **not** "an abstraction and an
interface" — it is composition, plus a dependency that only points one way.

### Two rules the tests enforce

1. **The abstraction composes its implementor.** No class inherits from the
   other hierarchy, and there is no `SmsOtpMessage` or `SvgCircle` anywhere.
2. **The implementor never mentions the abstraction.** Its methods take plain
   values, so a new message type cannot force a change to any channel.

### Example 1 — message × channel

`Message` knows *what* to say; `Channel` knows *how* to deliver it. Three
messages × three channels is nine combinations from **six** classes.

| File | Role |
|------|------|
| `bridge/notification/implementor.py` | `Channel` (ABC) + `SmsChannel`, `EmailChannel`, `PushChannel` |
| `bridge/notification/abstraction.py` | `Message` (ABC) + `OtpMessage`, `OrderShippedMessage`, `PaymentReceiptMessage` |
| `bridge/notification/center.py` | `NotificationCenter` — name → channel wiring, no policy |

The three channels disagree productively about the same three strings, and no
message has to care:

| Channel | Subject | Length rule | Recipient rule |
|---|---|---|---|
| SMS | folded into the body | refuses over 480 chars | must be E.164 (`+…`) |
| Email | kept as the subject | 100 000 | must contain a valid domain |
| Push | becomes the title, capped at 40 | 120 | must start with `device-` |

`Message.send()` is a template method: the flow (delegate to the implementor)
is fixed, the wording is what subclasses supply.

### Example 2 — shape × renderer

`Shape` knows its geometry; `Renderer` knows a format. Three shapes × three
renderers, again six classes.

| File | Role |
|------|------|
| `bridge/diagram/implementor.py` | `Renderer` (ABC) + `SvgRenderer`, `AsciiRenderer`, `JsonGeometryRenderer` |
| `bridge/diagram/abstraction.py` | `Shape` (ABC) + `Circle`, `Rectangle`, `Triangle`, plus the `Diagram` composition root |
| `bridge/diagram/legacy_exporter.py` | The "before" picture — one function branching on both axes |

The renderer's interface is **primitives only** — `draw_circle(radius)`,
`draw_rectangle(width, height)`, `draw_triangle(base, height)` — and never
`draw(shape)`. That is the load-bearing decision: a renderer written once
serves every shape that exists now and every shape added later, and a new
shape never needs a new renderer method.

`legacy_exporter.py` is the contrast. It takes `list[object]` because it
cannot express "some shape", and it chains `isinstance` per shape *inside*
each format branch — so both axes must be edited in the same function. The
tests assert the coupling is there, so the Bridge's benefit stays visible.

---

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
│   ├── registry.py               # registry + CheckoutService
│   └── demo.py                   # all six Adapter demos
├── bridge/
│   ├── __init__.py
│   ├── notification/
│   │   ├── implementor.py        # Channel: SMS, Email, Push
│   │   ├── abstraction.py        # Message: OTP, shipped, receipt
│   │   └── center.py             # NotificationCenter
│   ├── diagram/
│   │   ├── implementor.py        # Renderer: SVG, ASCII, JSON
│   │   ├── abstraction.py        # Shape: circle, rectangle, triangle
│   │   └── legacy_exporter.py    # no-Bridge anti-pattern
│   └── demo.py                   # both Bridge axes
├── tests/                        # 230 tests (169 Adapter, 61 Bridge)
├── main.py                       # pattern dispatcher
├── pyrightconfig.json            # strict source, lenient tests
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
| Bridge structure | no cross-hierarchy inheritance; `Channel.deliver` takes only `str`; no `SmsOtpMessage`-style classes exist |
| Bridge axes open | a `FaxChannel` and a `MaintenanceNotice` defined **in the test file** pair with all existing messages; a `Hexagon` and a `BrailleRenderer` pair with all existing shapes |
| Bridge behaviour | the full 3 × 3 grid in both examples; per-channel subject/length/recipient rules |
| Bridge implementor purity | `ast` parse proves the renderer module never references a `Shape` in code |
| The anti-pattern | `legacy_exporter` needs an `isinstance` branch per shape and rejects an unknown shape |

## Type Checking

`pyrightconfig.json` runs pyright in **strict** mode over `adapter/`, `bridge/`
and `main.py`, with the test directory excluded (pytest ships no type
information, and test fixtures are intentionally unannotated).

```bash
npx --yes pyright@latest        # or: pyright-langserver --stdio for the LSP
```

The project is clean at error level 2 and above. The `lsp` block in your
opencode config registers `pyright-langserver` so the editor panel reports the
same diagnostics.

## Conventions

- Python 3.10+
- Type hints everywhere, `from __future__ import annotations`
- `pytest` for testing
- snake_case for files and functions, PascalCase for classes
- Vendor SDKs are simulated in-repo so the demo needs no credentials
- `main.py` only dispatches; every pattern owns its own `demo.py`
