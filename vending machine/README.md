# Vending Machine — State Pattern

A thread-safe vending machine simulation. Every user action is routed through a
**State** object, so the machine's behaviour changes with its state instead of
being buried in `if/elif` chains inside the machine.

## Quick Start

```bash
cd "vending machine"     # note: the folder name contains a space
python main.py           # run the scenario demo
pytest tests/ -v         # run all tests (45)
```

## Design

### State Pattern

`VendingMachine` holds no branching logic. It forwards each event to
`self._current_state`, and the state decides what happens and which state comes next.

```
                    insert_coin
      ┌────────┐ ────────────────▶ ┌────────────┐
      │  Idle  │                   │ HasMoney   │
      └────────┘ ◀──────────────── └────────────┘
           ▲        cancel / dispense      │ select_product
           │                               ▼ (valid)
           │                        ┌─────────────┐
           │                        │ Dispensing  │
           │                        └─────────────┘
           │                               │ stock drained
           │                               ▼
           │                        ┌──────────────┐
           └────────────────────────│ OutOfStock   │
              restocked / partial   └──────────────┘
```

| State | Accepts | Rejects |
|-------|---------|---------|
| `IdleState` | `insert_coin` → `HasMoney` | `select_product`, `dispense`, `cancel` |
| `HasMoneyState` | `insert_coin`, `select_product` → `Dispensing` | — |
| `DispensingState` | `dispense` (decrement stock, return change) | `insert_coin`, `select_product`, `cancel` |
| `OutOfStockState` | nothing | everything |

### Components

| File | Responsibility |
|------|----------------|
| `models/coin.py` | `Coin` enum — NICKEL, DIME, QUARTER, DOLLAR |
| `models/product.py` | Stock unit; `decrement`/`restock`/`get_quantity` guarded by a lock |
| `services/vending_machine.py` | Context object: inventory, coin inventory, balance, state delegation |
| `states/state.py` | `State` ABC — the 4-event interface |
| `states/*.py` | The four concrete states |

### Supporting Techniques

- **Greedy change algorithm** — `return_change` walks denominations largest →
  smallest, capped by physical coin stock. It is *all-or-nothing*: if the exact
  amount cannot be made, nothing is debited and the caller gets `False`.
- **Automatic refund** — when change cannot be made, `DispensingState` refunds the
  full balance and calls `product.restock(1)`, so a failed dispense leaves no
  phantom sale.
- **Float hygiene** — `round2()` adds a `1e-9` epsilon before rounding so repeated
  `0.05 + 0.10 + ...` accumulation does not drift to `$0.34999999`.
- **Thread safety** — `VendingMachine` serialises all public actions with one
  non-reentrant lock; `Product` guards its own quantity with a separate lock so
  the stock check and the decrement inside `select_product` are atomic.

## Test Coverage

`tests/test_vending_machine.py` — 45 tests, 8 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestCoin` | Denomination values, enum identity |
| `TestProduct` | Quantity semantics, restock, concurrent decrement |
| `TestStateContract` | Every state implements `State`; `State` is not instantiable; state objects are reused, not rebuilt |
| `TestMachineBasics` | Inventory, balance arithmetic, `round2` epsilon |
| `TestIdleState` / `TestHasMoneyState` | Each rejected and accepted event per state |
| `TestSuccessfulPurchase` | Stock decrement, exact vs. overpayment, change debiting |
| `TestCancel` | Refund, balance reset, no stock movement |
| `TestOutOfStockState` | Auto-transition when drained; all events rejected |
| `TestChangeAlgorithm` | Greedy breakdown, inventory caps, unreachable amounts, no partial debit |
| `TestRefundOnFailedChange` | Restock on failed change |
| `TestThreadSafety` | Exact balance under 1600 concurrent coins; stock never negative; exact drain under sequential load |

## Known Behaviour Notes

These are deliberate consequences of the current design, covered by tests so
they cannot regress silently:

- **`OutOfStockState` is terminal.** Once *every* product hits zero the machine
  rejects all input. Restocking a product does not automatically return it to
  `Idle` — an admin restock plus an explicit state change is required.
- **Balance is cleared after every dispense.** A concurrent buyer can therefore
  lose the credit it inserted while another buyer's `select_product` cleared the
  shared balance. The test suite asserts the safety property (stock never goes
  negative) rather than a per-thread sale count.
- **`Product.decrement` does not floor at zero.** Stock can go negative if called
  directly; the state machine's quantity check is what prevents overselling.
- **The folder name contains a space**, so `cd "vending machine"` needs quoting.

## Structure

```
vending machine/
├── models/
│   ├── coin.py              # Coin enum
│   └── product.py           # Product + lock
├── services/
│   └── vending_machine.py   # VendingMachine context
├── states/
│   ├── state.py             # State ABC
│   ├── idle_state.py
│   ├── has_money_state.py
│   ├── dispensing_state.py
│   └── out_of_stock_state.py
├── tests/
│   └── test_vending_machine.py   # 45 tests
├── main.py
└── README.md
```

## Conventions

- Python 3.10+
- Type hints on the machine, plain types on state handlers
- `pytest` for testing
- snake_case for files and functions, PascalCase for classes
