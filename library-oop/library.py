from .book import Book
from .member import Member
from .librarian import Librarian


class Library:
    def __init__(self):
        self.books: list[Book] = []
        self.members: list[Member] = []
        self.librarians: list[Librarian] = []

    def add_book(self, book: Book):
        self.books.append(book)

    def add_member(self, member: Member):
        self.members.append(member)

    def add_librarian(self, librarian: Librarian):
        self.librarians.append(librarian)

    def find_book_by_id(self, book_id: int) -> Book | None:
        return next((book for book in self.books if book.book_id == book_id), None)

    def find_member_by_id(self, member_id: int) -> Member | None:
        return next((m for m in self.members if m.member_id == member_id), None)

    def find_book(self, title: str) -> Book | None:
        return next((book for book in self.books if book.title == title), None)

    def remove_book(self, book_id: int) -> bool:
        book = self.find_book_by_id(book_id)
        if book:
            self.books.remove(book)
            return True
        return False

    def list_books(self) -> list[str]:
        return [book.title for book in self.books]

    def list_members(self) -> list[str]:
        return [member.name for member in self.members]

    def list_librarians(self) -> list[str]:
        return [librarian.name for librarian in self.librarians]

    def borrow_book(self, member_id: int, book_id: int) -> bool:
        member = self.find_member_by_id(member_id)
        book = self.find_book_by_id(book_id)
        if not member or not book:
            return False
        if not book.is_available():
            return False
        book.borrow()
        member.borrow_book(book)
        return True

    def return_book(self, member_id: int, book_id: int) -> bool:
        member = self.find_member_by_id(member_id)
        book = self.find_book_by_id(book_id)
        if not member or not book:
            return False
        if book not in member.borrowed_books:
            return False
        book.return_book()
        member.return_book(book)
        return True
