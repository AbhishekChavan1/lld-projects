from datetime import datetime, timedelta

from models.book import Book
from models.loan import Loan
from models.member import Member
from services.library import LibraryService
from strategies.premium import PremiumPenalty


def main():
    library = LibraryService(penalty_strategy=PremiumPenalty(daily_rate=1.0))

    # Add books and members
    clean_code = Book("Clean Code", "Robert Martin", "978-0132350884")
    dune = Book("Dune", "Frank Herbert", "978-0441172719")
    library.add_book(clean_code)
    library.add_book(dune)

    alice = Member("Alice", "M001")
    bob = Member("Bob", "M002")
    library.add_member(alice)
    library.add_member(bob)

    # Search
    print("Search 'clean':", [b.title for b in library.search_by_title("clean")])

    # Checkout
    loan = library.checkout_book("M001", "978-0132350884")
    print("Alice checked out:", loan.book_isbn, "due:", loan.due_date.date())

    # Bob tries to check out the same (loaned) book -> fails, so he reserves it
    print("Bob checkout while loaned:", library.checkout_book("M002", "978-0132350884"))
    print("Bob reserved:", library.reserve_book("M002", "978-0132350884"))

    # Alice returns -> fine computed, reservation queue keeps book RESERVED for Bob
    result = library.return_book("M001", "978-0132350884")
    print(
        "Return -> days_overdue:",
        result["days_overdue"],
        "| fine:",
        result["fine"],
        "| status now:",
        clean_code.status.value,
    )

    # Bob picks up his reserved copy
    loan_bob = library.checkout_book("M002", "978-0132350884")
    print("Bob picked up reserved book:", loan_bob is not None)

    # Simulate an overdue return to show fines (backdated loan)
    overdue_loan = Loan(
        book_isbn="978-0441172719",
        member_id="M002",
        issue_date=datetime.now() - timedelta(days=25),
        due_date=datetime.now() - timedelta(days=11),
    )
    bob.add_loan(overdue_loan)
    result = library.return_book("M002", "978-0441172719")
    print(
        "Overdue return -> days_overdue:",
        result["days_overdue"],
        "| fine:",
        result["fine"],
        "| Bob unpaid fines:",
        bob.get_unpaid_fines(),
    )


if __name__ == "__main__":
    main()
