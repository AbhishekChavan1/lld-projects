class Book:
    def __init__(self, book_id: int, title: str, author: str, publication_year: int, genre: str, total_copies: int):
        self.book_id: int = book_id
        self.title: str = title
        self.author: str = author
        self.publication_year: int = publication_year
        self.genre: str = genre
        self.total_copies: int = total_copies

    @property
    def availability(self) -> bool:
        return self.total_copies > 0

    def borrow(self):
        if self.total_copies <= 0:
            raise ValueError(f"'{self.title}' is not available for borrowing.")
        self.total_copies -= 1

    def return_book(self):
        self.total_copies += 1

    def is_available(self) -> bool:
        return self.availability

    def __str__(self):
        return (
            f"Book ID: {self.book_id}, Title: {self.title}, Author: {self.author}, "
            f"Availability: {'Available' if self.availability else 'Not Available'}, "
            f"Publication Year: {self.publication_year}, Genre: {self.genre}, "
            f"Total Copies: {self.total_copies}"
        )
