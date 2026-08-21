class Member:
    def __init__(self, name, member_id):
        self.name = name
        self.member_id = member_id
        self.active_loans = []
        self.unpaid_fines = 0.0

    def can_checkout(self, fine_limit):
        return self.unpaid_fines < fine_limit

    def has_loan_for(self, isbn):
        return any(loan.book_isbn == isbn for loan in self.active_loans)

    def add_loan(self, loan):
        self.active_loans.append(loan)

    def remove_loan(self, loan):
        if loan in self.active_loans:
            self.active_loans.remove(loan)
            return True
        return False

    def get_active_loans(self):
        return list(self.active_loans)

    def add_fine(self, amount):
        self.unpaid_fines += amount

    def pay_fine(self, amount):
        if amount <= self.unpaid_fines:
            self.unpaid_fines -= amount
            return True
        return False

    def get_unpaid_fines(self):
        return self.unpaid_fines
