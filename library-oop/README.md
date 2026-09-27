# Library Management (OOP Exercise)

A library domain built around encapsulation and composition: books, members, and
loans collaborate through narrow public methods, and the fine policy is a
pluggable **Strategy**.

## Quick Start

```bash
cd library-oop
python main.py        # run the demo
pytest tests/ -v     # run all tests (14)
```

## Design

### Domain Model

```
LibraryService            <- orchestrates; owns the ISBN/member_id indexes
  ├── Book                <- title, author, isbn, status, reservation queue
  │     └── reservations  <- deque of Members waiting for a LOANED book
  ├── Member              <- active_loans, unpaid_fines
  │     └── Loan          <- book_isbn, member_id, issue_date, due_date, return_date
  └── Penalty (ABC)       <- calculate_fine(days_overdue)
        ├── StandardPenalty   flat rate
        └── PremiumPenalty    grace days, then double rate
```

No class reaches into another's internals. `Member` exposes `can_checkout`,
`has_loan_for`, `add_fine`, `pay_fine`; `Book` exposes `borrow`, `reserve`,
`mark_returned`, `next_reservation`. `get_active_loans()` and
`get_reservations()` both return **copies**, so callers cannot mutate internal
collections by accident.

### Book Status State Machine

`BookStatus` is a three-state enum with no illegal transitions:

```
                   reserve(member)
      AVAILABLE ────────────────────▶ RESERVED
          ▲                              │
          │                              │ checkout by next in queue
          │  return, queue empty         ▼
          ├────────────────────────── LOANED
          │                              │
          └────── return, queue not empty ──▶ RESERVED
```

`Book.borrow()` and `Book.mark_returned()` both guard on the current status and
return `False` rather than corrupting state.

### Reservation Queue

`Book.reservations` is a `collections.deque` — a FIFO waitlist.

- `reserve(member)` rejects a duplicate reservation and flips an `AVAILABLE`
  book to `RESERVED`.
- `next_reservation()` peeks the head of the queue.
- `remove_next_reservation()` pops the head; if the queue empties while the book
  is `RESERVED`, the book returns to `AVAILABLE`.
- `mark_returned()` sends a returned book to `RESERVED` if anyone is waiting,
  otherwise to `AVAILABLE`.

This is why the demo shows Alice returning a book that instantly becomes
`Reserved` for Bob.

### Penalty Strategies

`Penalty` is an ABC with one method, so the fine policy is swappable at
construction time:

| Strategy | Rule | 11 days overdue @ $1.00 |
|----------|------|-------------------------|
| `StandardPenalty(rate_per_day=1.0)` | `days * rate` | $11.00 |
| `PremiumPenalty(daily_rate=1.0, grace_days=5)` | `grace * rate + (days - grace) * rate * 2` | $17.00 |

Both clamp negative input to `0` via `max(0, days_overdue)`.

### Checkout Rules

`LibraryService.checkout_book` applies six ordered checks and returns `None` for
every rejection (rather than raising, since "cannot borrow" is expected
business flow):

1. Member and book both exist, else `ValueError`.
2. `unpaid_fines < fine_limit` (default $50).
3. The member does not already hold a loan for that ISBN.
4. The book is not `LOANED`.
5. If the book is `RESERVED`, this member is the head of the queue — and is
   popped off it as part of the checkout.
6. Mark `LOANED`, create the `Loan` with a due date of
   `issue_date + loan_period_days`, attach it to the member.

### Return Rules

`return_book` finds the member's active loan for that ISBN, marks it returned,
computes `days_overdue`, applies the penalty strategy, charges the fine, drops
the loan, and calls `book.mark_returned()`. It returns
`{"loan", "days_overdue", "fine"}`.

`Loan.days_overdue()` uses `return_date` when returned and `now` otherwise, then
clamps with `max(0, ...)` — so an early return is `0`, never negative.

### Search

Matching logic lives in two places on purpose: `LibraryService.search_by_*`
(indexed, for the app) and the static `Search` class in `services/search.py`
(works on any list of books, for batch jobs). Both are case-insensitive
substring matches; `search_by_isbn` is exact.

## Test Coverage

`tests/test_library.py` — 14 tests covering the Book status machine, the
reservation queue, member fine limits, loan overdue math, and the fine flow
end-to-end.

## Run It

```
Search 'clean': ['Clean Code']
Alice checked out: 978-0132350884 due: 2026-10-11
Bob checkout while loaned: None
Bob reserved: True
Return -> days_overdue: 0 | fine: 0.0 | status now: Reserved
Bob picked up reserved book: True
Overdue return -> days_overdue: 11 | fine: 17.0 | Bob unpaid fines: 17.0
```

## Structure

```
library-oop/
├── enums/
│   └── bookstatus.py        # BookStatus: AVAILABLE, LOANED, RESERVED
├── models/
│   ├── book.py              # Book + reservation deque
│   ├── member.py            # Member + fines
│   └── loan.py              # Loan + overdue math
├── strategies/
│   ├── penalty.py           # Penalty ABC
│   ├── standard.py          # StandardPenalty
│   └── premium.py           # PremiumPenalty
├── services/
│   ├── library.py           # LibraryService
│   └── search.py            # static Search helpers
├── tests/
│   └── test_library.py      # 14 tests
├── main.py
└── README.md
```

## Conventions

- Python 3.10+
- No type hints in this project (it is an OOP exercise, kept deliberately plain)
- `pytest` for testing
- snake_case for files and functions, PascalCase for classes
