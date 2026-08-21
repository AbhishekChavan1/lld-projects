from collections import deque

from enums.bookstatus import BookStatus


class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.status = BookStatus.AVAILABLE
        self.reservations = deque()

    def is_available(self):
        return self.status == BookStatus.AVAILABLE

    def borrow(self):
        if not self.is_available():
            return False
        self.status = BookStatus.LOANED
        return True

    def reserve(self, member):
        if member in self.reservations:
            return False
        self.reservations.append(member)
        if self.status == BookStatus.AVAILABLE:
            self.status = BookStatus.RESERVED
        return True

    def next_reservation(self):
        if self.reservations:
            return self.reservations[0]
        return None

    def remove_next_reservation(self):
        if self.reservations:
            self.reservations.popleft()
            if not self.reservations and self.status == BookStatus.RESERVED:
                self.status = BookStatus.AVAILABLE
            return True
        return False

    def get_reservations(self):
        return list(self.reservations)

    def mark_returned(self):
        if self.status == BookStatus.LOANED:
            if self.reservations:
                self.status = BookStatus.RESERVED
            else:
                self.status = BookStatus.AVAILABLE
            return True
        return False
