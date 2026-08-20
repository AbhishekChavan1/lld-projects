from .user import User


class Member(User):
    def __init__(self, user_id: int, name: str, email: str, member_id: int):
        super().__init__(user_id=user_id, name=name, email=email)
        self.member_id = member_id
        self.borrowed_books: list = []

    def borrow_book(self, book):
        self.borrowed_books.append(book)

    def return_book(self, book):
        if book in self.borrowed_books:
            self.borrowed_books.remove(book)
