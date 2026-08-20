# Library Management (OOP)

A simple library management system demonstrating OOP principles: inheritance, composition, and polymorphism.

## Features

- Book catalog with availability tracking
- Member registration and borrowing
- Librarian role with book management
- Borrow/return workflow with validation

## Structure

```
library-oop/
├── __init__.py
├── book.py          # Book entity with availability tracking
├── user.py          # Base User class
├── member.py        # Member extends User, can borrow/return
├── librarian.py     # Librarian extends User, manages books
├── library.py       # Library aggregate (books, members, librarians)
├── main.py          # Demo entry point
└── README.md
```

## Quick Start

```bash
cd projects/library-oop
python -m library-oop.main
```
