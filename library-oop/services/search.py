from models.book import Book


class Search:
    @staticmethod
    def search_by_title(books, title):
        return [b for b in books if title.lower() in b.title.lower()]

    @staticmethod
    def search_by_author(books, author):
        return [b for b in books if author.lower() in b.author.lower()]

    @staticmethod
    def search_by_isbn(books, isbn):
        return [b for b in books if isbn == b.isbn]
