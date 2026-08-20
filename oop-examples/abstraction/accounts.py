from abc import ABC, abstractmethod
from datetime import datetime


class Transaction:
    def __init__(self, operation, amount):
        self.operation = operation
        self.amount = amount
        self.timestamp = datetime.now()

    def __str__(self):
        return f"{self.timestamp} - {self.operation}: ${self.amount:.2f}"


class Account(ABC):
    def __init__(self, account_number, account_holder):
        self.account_number = account_number
        self.account_holder = account_holder
        self.balance = 0.0
        self.transactions = []

    @abstractmethod
    def deposit(self, amount):
        pass

    @abstractmethod
    def withdraw(self, amount):
        pass

    def get_balance(self):
        return self.balance

    def get_transactions(self):
        return self.transactions

    def get_account_info(self):
        return (
            f"Account Number: {self.account_number}, "
            f"Account Holder: {self.account_holder}, "
            f"Balance: ${self.balance:.2f}"
        )


class SavingsAccount(Account):
    MAX_WITHDRAWAL_LIMIT = 1000.0
    INTEREST_RATE = 0.02

    def __init__(self, account_number, account_holder, balance=0.0):
        super().__init__(account_number, account_holder)
        self.balance = balance
        self.__daily_withdrawal = 0
        self.__withdrawal_date = datetime.now().date()

    def _reset_daily_withdrawal_if_needed(self):
        if self.__withdrawal_date != datetime.now().date():
            self.__daily_withdrawal = 0
            self.__withdrawal_date = datetime.now().date()

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(Transaction("Deposit", amount))

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.balance:
            raise ValueError("Insufficient funds.")
        if amount > self.MAX_WITHDRAWAL_LIMIT:
            raise ValueError(
                f"Withdrawal amount exceeds daily limit of ${self.MAX_WITHDRAWAL_LIMIT}."
            )

        self._reset_daily_withdrawal_if_needed()

        if self.__daily_withdrawal + amount > self.MAX_WITHDRAWAL_LIMIT:
            raise ValueError(
                f"Daily withdrawal limit exceeded. "
                f"Current daily withdrawal: ${self.__daily_withdrawal}."
            )

        self.balance -= amount
        self.__daily_withdrawal += amount
        self.transactions.append(Transaction("Withdrawal", amount))

    def apply_interest(self):
        interest = self.balance * self.INTEREST_RATE
        self.balance += interest
        self.transactions.append(Transaction("Interest", interest))

    def get_daily_withdrawal(self):
        self._reset_daily_withdrawal_if_needed()
        return self.__daily_withdrawal

    def get_account_info(self):
        return f"Savings Account - {super().get_account_info()}"


class CurrentAccount(Account):
    OVERDRAFT_LIMIT = 5000.0

    def __init__(self, account_number, account_holder, balance=0.0):
        super().__init__(account_number, account_holder)
        self.balance = balance

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(Transaction("Deposit", amount))

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance - amount < -self.OVERDRAFT_LIMIT:
            raise ValueError(f"Overdraft limit of ${self.OVERDRAFT_LIMIT} exceeded.")
        self.balance -= amount
        self.transactions.append(Transaction("Withdrawal", amount))

    def get_account_info(self):
        return f"Current Account - {super().get_account_info()}"


class FixedDepositAccount(Account):
    INTEREST_RATE = 0.05

    def __init__(self, account_number, account_holder, maturity_date, balance=0.0):
        super().__init__(account_number, account_holder)
        self.balance = balance
        self.maturity_date = maturity_date

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(Transaction("Deposit", amount))

    def withdraw(self, amount):
        if datetime.now().date() < self.maturity_date:
            raise ValueError("Withdrawal not allowed before maturity date.")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        self.balance -= amount
        self.transactions.append(Transaction("Withdrawal", amount))

    def get_account_info(self):
        return f"Fixed Deposit Account - {super().get_account_info()}"

    def apply_interest(self):
        if datetime.now().date() >= self.maturity_date:
            interest = self.balance * self.INTEREST_RATE
            self.balance += interest
            self.transactions.append(Transaction("Interest", interest))

    def get_maturity_date(self):
        return self.maturity_date


class User:
    def __init__(self, name):
        self.name = name
        self.accounts = []

    def add_account(self, account):
        if not isinstance(account, Account):
            raise ValueError("Invalid account type.")
        self.accounts.append(account)

    def get_accounts(self):
        return self.accounts

    def get_user_info(self):
        return f"User: {self.name}, Accounts: {len(self.accounts)}"


def main():
    user = User("John Doe")
    savings_account = SavingsAccount("SA123", "John Doe", 5000.0)
    current_account = CurrentAccount("CA123", "John Doe", 2000.0)
    fixed_deposit_account = FixedDepositAccount(
        "FD123", "John Doe", datetime(2025, 1, 1).date(), 10000.0
    )
    user.add_account(savings_account)
    user.add_account(current_account)
    user.add_account(fixed_deposit_account)
    print(user.get_user_info())

    savings_account.deposit(1000)
    print(savings_account.get_account_info())
    savings_account.withdraw(500)
    print(savings_account.get_account_info())

    current_account.withdraw(2500)
    print(current_account.get_account_info())


if __name__ == "__main__":
    main()
