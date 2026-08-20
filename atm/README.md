# ATM Simulation

A Python implementation of an ATM (Automated Teller Machine) system demonstrating the **State Pattern** and **Composition**.

## Features

- Card insertion and PIN authentication
- Balance inquiry, withdrawals, and deposits
- PIN change functionality
- Transaction history tracking
- Card blocking after failed PIN attempts
- Cash dispensing with denomination optimization

## Design Patterns

- **State Pattern** — ATM transitions through `IDLE → CARD_INSERTED → AUTHENTICATED` states
- **Composition** — ATM is composed of `CardReader` and `CashDispenser` components

## Structure

```
atm/
├── core/
│   ├── __init__.py
│   ├── atm.py              # ATM class + ATMState enum
│   ├── card_reader.py      # CardReader component
│   └── cash_dispenser.py   # CashDispenser with denomination logic
├── models/
│   ├── __init__.py
│   ├── account.py          # Account entity
│   ├── card.py             # Card entity with PIN validation
│   ├── transactions.py     # Transaction record
│   └── transactiontypes.py # TransactionType enum
├── services/
│   ├── __init__.py
│   ├── atmservices.py      # ATMService facade
│   └── bank.py             # Bank card registry
├── tests/
│   └── test_atm.py         # 9 pytest tests
├── main.py                 # Demo entry point
└── README.md
```

## Quick Start

```bash
cd projects/atm
python main.py
```

## Running Tests

```bash
pytest tests/
```
