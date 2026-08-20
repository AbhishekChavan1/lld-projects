from .book import Book
from .member import Member
from .librarian import Librarian
from .library import Library


def main():
    lib = Library()

    book1 = Book(1, "1984", "George Orwell", 1949, "Dystopian", 3)
    book2 = Book(2, "To Kill a Mockingbird", "Harper Lee", 1960, "Fiction", 2)
    lib.add_book(book1)
    lib.add_book(book2)

    librarian = Librarian(1, "Alice", "alice@lib.com", library=lib)
    lib.add_librarian(librarian)

    book3 = Book(3, "The Great Gatsby", "F. Scott Fitzgerald", 1925, "Classic", 1)
    librarian.add_book(book3)

    member = Member(1, "Bob", "bob@email.com", member_id=101)
    lib.add_member(member)

    print("Available books:", lib.list_books())
    print()

    lib.borrow_book(101, 1)
    print(f"{member.name} borrowed: {[b.title for b in member.borrowed_books]}")
    print(f"Copies of '1984' remaining: {book1.total_copies}")
    print()

    lib.return_book(101, 1)
    print(f"Copies of '1984' after return: {book1.total_copies}")
    print(f"{member.name} borrowed: {[b.title for b in member.borrowed_books]}")
    print()

    print("Librarians:", lib.list_librarians())
    print("Members:", lib.list_members())


if __name__ == "__main__":
    main()
