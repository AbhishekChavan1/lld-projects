# Coffee Machine — Decorator + State Patterns

A configurable beverage machine. Drink customisation uses the **Decorator**
pattern, the machine lifecycle uses the **State** pattern, and ingredient
stocking is thread-safe.

## Quick Start

```bash
cd coffee-machine
python main.py           # run the four scenario demos
pytest tests/ -v         # run all tests (51)
```

## Design

### Decorator Pattern — building the order

`Beverage` is the common interface. Base drinks (`Espresso`, `Americano`)
implement it directly; each condiment wraps *any* `Beverage` and adds its own
cost, description fragment, and recipe entry.

```
SugarDecorator
   └─ MilkDecorator
        └─ Espresso          cost 2.00
   +0.20  +0.50
= "Espresso, Milk, Sugar"  $2.70
recipe: {coffee_beans: 1, water: 1, milk: 1, sugar: 1}
```

| Decorator | Adds cost | Adds to recipe |
|-----------|-----------|----------------|
| `MilkDecorator` | $0.50 | `milk` |
| `SugarDecorator` | $0.20 | `sugar` |
| `CaramelSyrupDecorator` | $0.60 | `caramel_syrup` |

Because `BeverageDecorator` extends `Beverage`, decorators compose to any depth
and a decorated drink is indistinguishable from a plain one to the machine.
Adding a new condiment means writing one class and touching nothing else.

### State Pattern — machine lifecycle

`CoffeeMachine` is a pure context object: it holds state and cash, and forwards
every public call to the current state. The three states reject illegal
transitions with a message rather than silently doing nothing.

```
   select_beverage
Idle ──────────────▶ PaymentPending
 ▲                        │ insert_coin until total >= cost
 │  brew complete         ▼
 └──────────────────── Brewing
        (or refund → Idle on missing ingredients)
```

| State | `select_beverage` | `insert_coin` | `brew` |
|-------|-------------------|----------------|--------|
| `IdleState` | → `PaymentPending` | rejected | rejected |
| `PaymentPendingState` | rejected | accumulates; → `Brewing` at cost | rejected |
| `BrewingState` | rejected | rejected | dispenses → `Idle` |

### Supporting Techniques

- **Inventory as a separate service** — `Inventory` is a `threading.RLock`
  guarded ingredient register, injected into `CoffeeMachine` so tests and
  machines can share or stub stock.
- **All-or-nothing consume** — `Inventory.consume` validates the whole recipe
  before decrementing, so a missing ingredient never leaves a half-consumed
  order. `has_ingredients` + `consume` are checked separately by `BrewingState`
  to enable the refund path.
- **Automatic refund** — if the recipe cannot be satisfied at brew time the
  machine refunds the full inserted cash, clears the selection, and returns to
  `Idle`, leaving inventory untouched.
- **`RLock` on the machine** — reentrant, so state handlers can safely call
  other `CoffeeMachine` methods while an action is already in flight.

## Test Coverage

`tests/test_coffee_machine.py` — 51 tests, 9 groups:

| Group | What it pins down |
|-------|-------------------|
| `TestBeverageContract` | ABCs are not instantiable; a brand-new `Beverage` subclass works without touching the machine |
| `TestBaseBeverages` | Base costs, descriptions, recipes; `get_recipe()` returns a fresh dict each call |
| `TestDecorators` | Per-decorator cost/description/recipe, stacking, order-independence of cost, duplicate decorators, three-deep stacks, no shared recipe state |
| `TestInventory` | Sufficiency checks, atomic consume, restock, snapshot isolation, 500 concurrent consumes never go negative |
| `TestStateContract` | `CoffeeMachineState` is abstract; all three states implement it |
| `TestIdleState` | Initial state, selection moves forward, out-of-order coin/brew rejected |
| `TestPaymentPendingState` | Partial accumulation, exact and over payment, re-selection rejected, brew before full payment rejected and consumes nothing |
| `TestBrewingState` | Ingredient consumption, change, context reset, decorated drinks, in-flight rejections |
| `TestInsufficientIngredients` | Refund path, nothing consumed on failure, restock recovery |
| `TestThreadSafety` | Serialised `brew`, no double refund under a 20-thread refund stampede, no lost cash across 20 concurrent coin insertions |

## Known Behaviour Notes

Deliberate consequences of the current design, covered by tests so they cannot
regress silently:

- **The flow is strictly serial.** A successful `brew` returns the machine to
  `Idle` with cash and selection cleared, so concurrent `brew()` calls on one
  machine produce exactly one drink — the rest are rejected by `IdleState`. The
  suite asserts the serialisation guarantee rather than throughput.
- **Coins are refused once payment completes.** `PaymentPendingState` hands off
  to `BrewingState` the moment `total >= cost`, and `BrewingState` rejects
  further coins, so overpayment must be delivered as a single amount.
- **`Inventory.has_ingredients` + `consume` are two lock acquisitions.** Safe
  here because the machine holds its own lock across the whole `brew`, but a
  caller bypassing `CoffeeMachine` could interleave.
- **Imports are mixed** — `decorators/beverage_decorator.py` and
  `services/inventory.py` use absolute imports while sibling modules use
  relative ones. Both work; it is just inconsistent.

## Structure

```
coffee-machine/
├── models/
│   ├── beverage.py          # Beverage ABC
│   ├── espresso.py          # Espresso
│   └── americano.py         # Americano
├── decorators/
│   ├── beverage_decorator.py        # BeverageDecorator ABC
│   ├── milk_decorator.py
│   ├── sugar_decorator.py
│   └── caramel_syrup_decorator.py
├── services/
│   └── inventory.py         # thread-safe ingredient register
├── states/
│   ├── coffee_machine_state.py      # ABC
│   ├── idle_state.py
│   ├── payment_pending_state.py
│   └── brewing_state.py
├── machine/
│   └── coffee_machine.py    # context object
├── tests/
│   └── test_coffee_machine.py       # 51 tests
├── main.py
└── README.md
```

## Conventions

- Python 3.10+ (`X | None` unions, `dict[str, int]` generics)
- Type hints everywhere
- `pytest` for testing
- snake_case for files and functions, PascalCase for classes
