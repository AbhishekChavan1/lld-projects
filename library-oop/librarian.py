from __future__ import annotations

from typing import TYPE_CHECKING

from .user import User
from .book import Book

if TYPE_CHECKING:
    from .library import Library


class Librarian(User):
    def __init__(self, user_id: int, name: str, email: str, library: Library | None = None):
        super().__init__(user_id=user_id, name=name, email=email)
        self.role = "Librarian"
        self.library = library

    def add_book(self, book: Book):
        if self.library:
            self.library.add_book(book)
        print(f"{self.name} added the book: {book.title}")

    def remove_book(self, book_id: int):
        if self.library:
            self.library.remove_book(book_id)
        print(f"{self.name} removed book ID: {book_id}")
