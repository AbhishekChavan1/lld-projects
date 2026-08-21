from datetime import datetime, timedelta

from enums.bookstatus import BookStatus
from models.loan import Loan


class LibraryService:
    def __init__(
        self,
        penalty_strategy,
        fine_limit: float = 50.0,
        loan_period_days: int = 14,
    ):
        self.books = {}
        self.members = {}
        self.penalty_strategy = penalty_strategy
        self.fine_limit = fine_limit
        self.loan_period_days = loan_period_days

    def add_book(self, book):
        if book.isbn in self.books:
            raise ValueError("Book already exists")
        self.books[book.isbn] = book

    def add_member(self, member):
        if member.member_id in self.members:
            raise ValueError("Member already exists")
        self.members[member.member_id] = member

    def reserve_book(self, member_id, isbn):
        member = self.members.get(member_id)
        book = self.books.get(isbn)
        if member is None:
            raise ValueError("Member not found")
        if book is None:
            raise ValueError("Book not found")
        return book.reserve(member)

    def checkout_book(self, member_id: str, isbn: str):
        member = self.members.get(member_id)
        book = self.books.get(isbn)
        if member is None:
            raise ValueError("Member not found")
        if book is None:
            raise ValueError("Book not found")

        # Step 1: Fine check
        if not member.can_checkout(self.fine_limit):
            return None

        # Step 2: No duplicate loans of the same book
        if member.has_loan_for(isbn):
            return None

        # Step 3: Availability / reservation check
        if book.status == BookStatus.LOANED:
            return None
        if book.status == BookStatus.RESERVED:
            next_member = book.next_reservation()
            if next_member is None or next_member.member_id != member_id:
                return None
            book.remove_next_reservation()

        # Step 4: Mark book as loaned
        book.status = BookStatus.LOANED

        # Step 5: Create loan
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=self.loan_period_days)
        loan = Loan(
            book_isbn=isbn,
            member_id=member_id,
            issue_date=issue_date,
            due_date=due_date,
        )

        # Step 6: Add loan to member
        member.add_loan(loan)
        return loan

    def return_book(self, member_id: str, isbn: str):
        member = self.members.get(member_id)
        book = self.books.get(isbn)
        if member is None:
            raise ValueError("Member not found")
        if book is None:
            raise ValueError("Book not found")

        loan = next(
            (l for l in member.active_loans if l.book_isbn == isbn), None
        )
        if loan is None or loan.is_returned():
            return None

        loan.mark_as_returned()
        days_overdue = loan.days_overdue()
        fine = self.penalty_strategy.calculate_fine(days_overdue)
        if fine > 0:
            member.add_fine(fine)

        member.remove_loan(loan)
        book.mark_returned()
        return {"loan": loan, "days_overdue": days_overdue, "fine": fine}

    def search_by_title(self, title):
        return [b for b in self.books.values() if title.lower() in b.title.lower()]

    def search_by_author(self, author):
        return [b for b in self.books.values() if author.lower() in b.author.lower()]

    def search_by_isbn(self, isbn):
        return self.books.get(isbn)
