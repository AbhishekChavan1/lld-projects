from datetime import datetime, timedelta


class Loan:
    def __init__(self, book_isbn, member_id, issue_date=None, due_date=None):
        self.book_isbn = book_isbn
        self.member_id = member_id
        self.issue_date = issue_date if issue_date else datetime.now()
        self.due_date = due_date if due_date else self.issue_date + timedelta(days=14)
        self.return_date = None

    def is_returned(self):
        return self.return_date is not None

    def mark_as_returned(self):
        self.return_date = datetime.now()

    def days_overdue(self):
        if self.is_returned():
            reference = self.return_date
        else:
            reference = datetime.now()
        overdue = (reference - self.due_date).days
        return max(0, overdue)

    def is_overdue(self):
        return not self.is_returned() and datetime.now() > self.due_date
