from datetime import date, datetime, timedelta

import pytest

from abstraction.accounts import (
    Account,
    CurrentAccount,
    FixedDepositAccount,
    SavingsAccount,
    Transaction,
    User,
)

TOMORROW = date.today() + timedelta(days=1)
YESTERDAY = date.today() - timedelta(days=1)


@pytest.fixture
def savings():
    return SavingsAccount("SA123", "John Doe", 5000.0)


@pytest.fixture
def current():
    return CurrentAccount("CA123", "John Doe", 2000.0)


@pytest.fixture
def matured_fd():
    return FixedDepositAccount("FD123", "John Doe", YESTERDAY, 10000.0)


class TestTransaction:
    def test_records_operation_amount_and_timestamp(self):
        txn = Transaction("Deposit", 100.0)
        assert txn.operation == "Deposit"
        assert txn.amount == 100.0
        assert isinstance(txn.timestamp, datetime)

    def test_str_includes_all_three_fields(self):
        txn = Transaction("Withdrawal", 25.5)
        text = str(txn)
        assert "Withdrawal" in text
        assert "$25.50" in text
        assert str(txn.timestamp) in text


class TestAccountAbstraction:
    def test_account_is_abstract(self):
        with pytest.raises(TypeError):
            Account("A1", "John")

    def test_every_concrete_account_implements_the_contract(self):
        for account in (
            SavingsAccount("SA1", "John"),
            CurrentAccount("CA1", "John"),
            FixedDepositAccount("FD1", "John", YESTERDAY),
        ):
            assert isinstance(account, Account)
            assert account.get_balance() == 0.0
            assert account.get_transactions() == []

    def test_base_class_provides_shared_info(self):
        account = CurrentAccount("CA1", "John Doe", 100.0)
        info = account.get_account_info()
        assert "CA1" in info
        assert "John Doe" in info
        assert "$100.00" in info

    def test_subclasses_prefix_the_shared_info(self, savings, current, matured_fd):
        assert savings.get_account_info().startswith("Savings Account - ")
        assert current.get_account_info().startswith("Current Account - ")
        assert matured_fd.get_account_info().startswith("Fixed Deposit Account - ")


class TestDeposit:
    @pytest.mark.parametrize("account_type", ["savings", "current", "fd"])
    def test_deposit_increases_balance(self, account_type, savings, current, matured_fd):
        account = {"savings": savings, "current": current, "fd": matured_fd}[account_type]
        account.deposit(500.0)
        assert account.get_balance() == account.get_balance()
        assert account.get_balance() > 0

    def test_deposit_is_recorded(self, savings):
        savings.deposit(1000.0)
        assert len(savings.get_transactions()) == 1
        assert savings.get_transactions()[0].operation == "Deposit"

    def test_zero_deposit_is_rejected(self, savings):
        with pytest.raises(ValueError, match="Deposit amount must be positive."):
            savings.deposit(0)

    def test_negative_deposit_is_rejected(self, savings):
        with pytest.raises(ValueError, match="Deposit amount must be positive."):
            savings.deposit(-100)

    def test_rejected_deposit_leaves_no_trace(self, savings):
        balance = savings.get_balance()
        with pytest.raises(ValueError):
            savings.deposit(-100)
        assert savings.get_balance() == balance
        assert savings.get_transactions() == []


class TestSavingsWithdrawalRules:
    def test_successful_withdrawal(self, savings):
        savings.withdraw(500)
        assert savings.get_balance() == 4500.0
        assert savings.get_transactions()[0].operation == "Withdrawal"

    def test_zero_withdrawal_is_rejected(self, savings):
        with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
            savings.withdraw(0)

    def test_negative_withdrawal_is_rejected(self, savings):
        with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
            savings.withdraw(-100)

    def test_overdraft_is_rejected(self, savings):
        with pytest.raises(ValueError, match="Insufficient funds."):
            savings.withdraw(99999)

    def test_amount_above_daily_limit_is_rejected(self, savings):
        with pytest.raises(
            ValueError, match=r"exceeds daily limit of \$1000\.0"
        ):
            savings.withdraw(1000.01)

    def test_exactly_the_daily_limit_is_allowed(self, savings):
        savings.withdraw(1000.0)
        assert savings.get_balance() == 4000.0

    def test_daily_limit_accumulates_across_withdrawals(self, savings):
        savings.withdraw(600)
        savings.withdraw(400)
        assert savings.get_daily_withdrawal() == 1000

    def test_cumulative_daily_limit_is_enforced(self, savings):
        savings.withdraw(600)
        savings.withdraw(400)
        with pytest.raises(ValueError, match="Daily withdrawal limit exceeded."):
            savings.withdraw(1)

    def test_cumulative_limit_message_reports_the_running_total(self, savings):
        savings.withdraw(600)
        savings.withdraw(400)
        with pytest.raises(ValueError, match=r"Current daily withdrawal: \$1000"):
            savings.withdraw(1)

    def test_daily_limit_message_reports_the_running_total(self, savings):
        savings.withdraw(1000.0)
        with pytest.raises(ValueError, match=r"Current daily withdrawal: \$1000\.0"):
            savings.withdraw(1)

    def test_rejected_withdrawal_does_not_change_balance(self, savings):
        savings.withdraw(1000.0)
        balance = savings.get_balance()
        with pytest.raises(ValueError):
            savings.withdraw(1)
        assert savings.get_balance() == balance

    def test_daily_withdrawal_starts_at_zero(self, savings):
        assert savings.get_daily_withdrawal() == 0

    def test_daily_withdrawal_resets_when_the_date_rolls_over(self, savings):
        savings.withdraw(500)
        assert savings.get_daily_withdrawal() == 500
        savings._SavingsAccount__withdrawal_date = YESTERDAY
        assert savings.get_daily_withdrawal() == 0

    def test_withdrawal_available_again_after_reset(self, savings):
        savings.withdraw(1000.0)
        savings._SavingsAccount__withdrawal_date = YESTERDAY
        savings.withdraw(1000.0)
        assert savings.get_balance() == 3000.0

    def test_daily_withdrawal_is_mangled(self, savings):
        assert hasattr(savings, "_SavingsAccount__daily_withdrawal")
        assert not hasattr(savings, "__daily_withdrawal")


class TestSavingsInterest:
    def test_interest_is_two_percent(self, savings):
        savings.apply_interest()
        assert savings.get_balance() == 5100.0

    def test_interest_is_recorded(self, savings):
        savings.apply_interest()
        assert savings.get_transactions()[-1].operation == "Interest"

    def test_interest_compounds(self, savings):
        savings.apply_interest()
        savings.apply_interest()
        assert savings.get_balance() == pytest.approx(5202.0)

    def test_interest_on_zero_balance(self):
        account = SavingsAccount("SA1", "John")
        account.apply_interest()
        assert account.get_balance() == 0.0


class TestCurrentAccountRules:
    def test_successful_withdrawal(self, current):
        current.withdraw(500)
        assert current.get_balance() == 1500.0

    def test_overdraft_is_permitted(self, current):
        current.withdraw(2500)
        assert current.get_balance() == -500.0

    def test_withdrawal_past_the_overdraft_limit_is_rejected(self, current):
        """The limit caps how negative the balance may get, not the amount."""
        with pytest.raises(
            ValueError, match=r"Overdraft limit of \$5000\.0 exceeded."
        ):
            current.withdraw(7000.01)

    def test_exactly_the_overdraft_limit_is_allowed(self, current):
        current.withdraw(7000.0)
        assert current.get_balance() == -5000.0

    def test_withdrawal_that_stays_inside_the_limit_is_allowed(self, current):
        current.withdraw(5001.0)
        assert current.get_balance() == -3001.0

    def test_negative_withdrawal_is_rejected(self, current):
        with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
            current.withdraw(-100)

    def test_savings_rejects_what_current_allows(self, savings, current):
        amount = 2500.0
        with pytest.raises(ValueError):
            savings.withdraw(amount)
        current.withdraw(amount)
        assert current.get_balance() == -500.0


class TestFixedDepositRules:
    def test_withdrawal_before_maturity_is_rejected(self):
        account = FixedDepositAccount("FD1", "John", TOMORROW, 10000.0)
        with pytest.raises(
            ValueError, match="Withdrawal not allowed before maturity date."
        ):
            account.withdraw(100)

    def test_withdrawal_after_maturity_is_allowed(self, matured_fd):
        matured_fd.withdraw(1000)
        assert matured_fd.get_balance() == 9000.0

    def test_maturity_is_checked_before_the_amount(self):
        account = FixedDepositAccount("FD1", "John", TOMORROW, 10000.0)
        with pytest.raises(ValueError, match="not allowed before maturity"):
            account.withdraw(-5)

    def test_negative_withdrawal_is_rejected_after_maturity(self, matured_fd):
        with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
            matured_fd.withdraw(-5)

    def test_no_insufficient_funds_check(self, matured_fd):
        matured_fd.withdraw(99999)
        assert matured_fd.get_balance() == 10000.0 - 99999

    def test_interest_before_maturity_is_skipped(self):
        account = FixedDepositAccount("FD1", "John", TOMORROW, 10000.0)
        account.apply_interest()
        assert account.get_balance() == 10000.0
        assert account.get_transactions() == []

    def test_interest_after_maturity_is_five_percent(self, matured_fd):
        matured_fd.apply_interest()
        assert matured_fd.get_balance() == 10500.0

    def test_interest_after_maturity_is_recorded(self, matured_fd):
        matured_fd.apply_interest()
        assert matured_fd.get_transactions()[-1].operation == "Interest"

    def test_maturity_date_is_readable(self, matured_fd):
        assert matured_fd.get_maturity_date() == YESTERDAY


class TestUser:
    def test_user_starts_with_no_accounts(self):
        assert User("John").get_accounts() == []
        assert User("John").get_user_info() == "User: John, Accounts: 0"

    def test_add_account(self, savings, current):
        user = User("John")
        user.add_account(savings)
        user.add_account(current)
        assert user.get_accounts() == [savings, current]
        assert user.get_user_info() == "User: John, Accounts: 2"

    def test_non_account_is_rejected(self):
        user = User("John")
        with pytest.raises(ValueError, match="Invalid account type."):
            user.add_account("not an account")

    def test_rejected_account_is_not_stored(self):
        user = User("John")
        with pytest.raises(ValueError):
            user.add_account(42)
        assert user.get_accounts() == []

    def test_get_accounts_returns_the_live_list(self, savings):
        """Documented encapsulation gap: the caller can mutate internal state."""
        user = User("John")
        user.add_account(savings)
        accounts = user.get_accounts()
        accounts.append("injected")
        assert len(user.get_accounts()) == 2

    def test_account_transactions_are_not_copied(self, savings):
        """Same gap on Account.get_transactions()."""
        savings.deposit(100)
        transactions = savings.get_transactions()
        transactions.clear()
        assert savings.get_transactions() == []
