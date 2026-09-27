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
cd oop-examples

python encapsulation/car_engine.py
python abstraction/accounts.py
python composition/employee.py
pytest tests/ -v     # 116 tests
```

## Tests

`tests/` — 116 tests, one file per example.

| File | Tests | What it pins down |
|------|-------|-------------------|
| `test_encapsulation.py` | 31 | Name mangling of `__state`/`__pressure`/`__engine`/`__wheels`, the full engine state machine (`OFF → IDLE → RUNNING → OFF`) including every rejected transition, wheel pressure validation, `Car` delegation |
| `test_abstraction.py` | 54 | `Account` is abstract, deposit/withdraw rules per account type, savings daily-withdrawal accumulation and date rollover, interest accrual, current-account overdraft ceiling, fixed-deposit maturity gate, `User` account validation |
| `test_composition.py` | 31 | `Payable`/`Reportable`/`Manageable` ABCs, per-role capability matrix, tax and reporting services injected rather than hardcoded, name mangling on `Employee`/`Manager`/`Contractor` |

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
├── tests/
│   ├── __init__.py
│   ├── test_encapsulation.py   # 31 tests
│   ├── test_abstraction.py     # 54 tests
│   └── test_composition.py     # 31 tests
└── README.md
```

## Known Behaviour Notes

Deliberate consequences of the current design, covered by tests so they cannot
regress silently:

- **`EngineState.OVERHEATED` is unreachable.** No public method sets it, and
  name mangling keeps callers from forcing it. It is a placeholder for an
  overheat sensor that does not exist yet.
- **The savings daily limit is enforced twice.** `withdraw` checks both
  `amount > MAX_WITHDRAWAL_LIMIT` and `daily + amount > MAX_WITHDRAWAL_LIMIT`.
  The second is the binding constraint; the first only changes the error message.
- **`CurrentAccount.OVERDRAFT_LIMIT` caps the balance, not the amount.** From a
  $2000 balance, withdrawing $5001 is legal (balance lands at −$3001); the
  rejection triggers past $7000.
- **`FixedDepositAccount` has no insufficient-funds check.** After maturity it
  will happily take a balance negative.
- **`get_transactions()` and `get_accounts()` return the live lists.** Callers
  can mutate internal state through them — unlike `Manager.get_reports()`,
  which correctly returns a copy.
- **The maturity check runs before the amount check** in
  `FixedDepositAccount.withdraw`, so a negative amount on an immature account
  reports the maturity error, not the amount error.
