import unittest
from datetime import datetime, timedelta

from enums.bookstatus import BookStatus
from models.book import Book
from models.loan import Loan
from models.member import Member
from services.library import LibraryService
from strategies.premium import PremiumPenalty
from strategies.standard import StandardPenalty


def make_library():
    lib = LibraryService(penalty_strategy=PremiumPenalty(daily_rate=1.0))
    lib.add_book(Book("Clean Code", "Robert Martin", "ISBN-1"))
    lib.add_book(Book("Dune", "Frank Herbert", "ISBN-2"))
    lib.add_member(Member("Alice", "M001"))
    lib.add_member(Member("Bob", "M002"))
    return lib


class TestCheckout(unittest.TestCase):
    def test_checkout_success(self):
        lib = make_library()
        loan = lib.checkout_book("M001", "ISBN-1")
        self.assertIsNotNone(loan)
        self.assertEqual(lib.books["ISBN-1"].status, BookStatus.LOANED)
        self.assertEqual(len(lib.members["M001"].active_loans), 1)

    def test_checkout_unknown_member_or_book(self):
        lib = make_library()
        with self.assertRaises(ValueError):
            lib.checkout_book("NOPE", "ISBN-1")
        with self.assertRaises(ValueError):
            lib.checkout_book("M001", "NOPE")

    def test_cannot_checkout_loaned_book(self):
        lib = make_library()
        lib.checkout_book("M001", "ISBN-1")
        self.assertIsNone(lib.checkout_book("M002", "ISBN-1"))

    def test_no_duplicate_loan(self):
        lib = make_library()
        lib.books["ISBN-1"].status = BookStatus.AVAILABLE
        lib.checkout_book("M001", "ISBN-1")
        # force status back so the availability check passes
        lib.books["ISBN-1"].status = BookStatus.AVAILABLE
        self.assertIsNone(lib.checkout_book("M001", "ISBN-1"))

    def test_blocked_by_fines(self):
        lib = make_library()
        lib.members["M001"].add_fine(100.0)
        self.assertIsNone(lib.checkout_book("M001", "ISBN-1"))


class TestReservations(unittest.TestCase):
    def test_reserve_and_pickup(self):
        lib = make_library()
        lib.checkout_book("M001", "ISBN-1")
        self.assertTrue(lib.reserve_book("M002", "ISBN-1"))
        # someone else cannot take the reserved book
        lib.add_member(Member("Carol", "M003"))
        self.assertIsNone(lib.checkout_book("M003", "ISBN-1"))
        # return frees it for Bob only (stays RESERVED for him)
        lib.return_book("M001", "ISBN-1")
        self.assertEqual(lib.books["ISBN-1"].status, BookStatus.RESERVED)
        self.assertIsNotNone(lib.checkout_book("M002", "ISBN-1"))

    def test_no_double_reservation(self):
        lib = make_library()
        lib.checkout_book("M001", "ISBN-1")
        self.assertTrue(lib.reserve_book("M002", "ISBN-1"))
        self.assertFalse(lib.reserve_book("M002", "ISBN-1"))


class TestReturnsAndFines(unittest.TestCase):
    def test_return_on_time_no_fine(self):
        lib = make_library()
        lib.checkout_book("M001", "ISBN-1")
        result = lib.return_book("M001", "ISBN-1")
        self.assertEqual(result["fine"], 0.0)
        self.assertEqual(result["days_overdue"], 0)
        self.assertEqual(lib.books["ISBN-1"].status, BookStatus.AVAILABLE)

    def test_return_unknown_loan(self):
        lib = make_library()
        self.assertIsNone(lib.return_book("M001", "ISBN-1"))

    def test_overdue_fine_premium(self):
        lib = make_library()
        overdue = Loan(
            book_isbn="ISBN-2",
            member_id="M001",
            issue_date=datetime.now() - timedelta(days=25),
            due_date=datetime.now() - timedelta(days=11),
        )
        lib.members["M001"].add_loan(overdue)
        result = lib.return_book("M001", "ISBN-2")
        # 11 days overdue: 5*1 + 6*2 = 17
        self.assertEqual(result["days_overdue"], 11)
        self.assertAlmostEqual(result["fine"], 17.0)
        self.assertAlmostEqual(lib.members["M001"].get_unpaid_fines(), 17.0)


class TestStrategies(unittest.TestCase):
    def test_standard(self):
        s = StandardPenalty(rate_per_day=2.0)
        self.assertEqual(s.calculate_fine(0), 0.0)
        self.assertEqual(s.calculate_fine(3), 6.0)

    def test_premium(self):
        p = PremiumPenalty(daily_rate=1.0)
        self.assertEqual(p.calculate_fine(5), 5.0)
        self.assertEqual(p.calculate_fine(7), 9.0)  # 5*1 + 2*2

    def test_strategies_are_interchangeable(self):
        for strategy in (StandardPenalty(), PremiumPenalty()):
            lib = LibraryService(penalty_strategy=strategy)
            lib.add_book(Book("X", "Y", "I"))
            lib.add_member(Member("A", "M"))
            loan = Loan(
                book_isbn="I",
                member_id="M",
                issue_date=datetime.now() - timedelta(days=20),
                due_date=datetime.now() - timedelta(days=10),
            )
            lib.members["M"].add_loan(loan)
            result = lib.return_book("M", "I")
            self.assertGreaterEqual(result["fine"], 0.0)


class TestSearch(unittest.TestCase):
    def test_search(self):
        lib = make_library()
        self.assertEqual(len(lib.search_by_title("dune")), 1)
        self.assertEqual(len(lib.search_by_author("martin")), 1)
        self.assertEqual(lib.search_by_isbn("ISBN-1").title, "Clean Code")


if __name__ == "__main__":
    unittest.main()
