from enum import Enum

from .card_reader import CardReader
from .cash_dispenser import CashDispenser
from ..models.transactions import Transaction
from ..models.transactiontypes import TransactionType

class ATMState(Enum):
    IDLE="idle"
    CARD_INSERTED="card_inserted"
    AUTHENTICATED="authenticated"
    TRANSACTION="transaction"

class ATM:

    MAX_PIN_ATTEMPTS = 3

    def __init__(self, bank):
        self.bank = bank
        self.card_reader = CardReader()
        self.cash_dispenser = CashDispenser()
        self.current_card = None
        self.current_account = None
        self.state = ATMState.IDLE
        self.transactions = []
        self._transaction_counter = 0

    def insert_card(self, card_number):
        if self.state != ATMState.IDLE:
            raise ValueError("ATM is currently busy")
        card = self.bank.get_card(card_number)
        if card is None:
            raise ValueError("Invalid card")
        if card.is_blocked:
            raise ValueError("Card is blocked")
        self.current_card = self.card_reader.insert_card(card)
        self.state = ATMState.CARD_INSERTED

    def authenticate(self, pin):
        if self.state != ATMState.CARD_INSERTED:
            raise ValueError("Insert card first")
        if not self.current_card.validate_pin(pin):
            if self.current_card.register_failed_attempt() >= self.MAX_PIN_ATTEMPTS:
                self.current_card.block()
                self.eject_card()
                raise ValueError("Card blocked after too many failed attempts")
            raise ValueError("Incorrect PIN")
        self.current_card.reset_failed_attempts()
        self.current_account = self.current_card.account
        self.state = ATMState.AUTHENTICATED

    def check_balance(self):
        self._require_authenticated()
        return self.current_account.get_balance()

    def withdraw(self, amount):
        self._require_authenticated()
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.current_account.balance:
            raise ValueError("Insufficient balance")
        notes = self.cash_dispenser.dispense_cash(amount)
        self.current_account.withdraw(amount)
        self._record_transaction(TransactionType.WITHDRAWAL, -amount, f"Dispensed: {self._describe_notes(notes)}")
        return notes

    def deposit(self, amount):
        self._require_authenticated()
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.current_account.deposit(amount)
        self._record_transaction(TransactionType.DEPOSIT, amount, "Cash deposit")

    def change_pin(self, old_pin, new_pin):
        self._require_authenticated()
        if not self.current_card.change_pin(old_pin, new_pin):
            raise ValueError("Incorrect PIN")
        self._record_transaction(TransactionType.PIN_CHANGE, 0, "PIN changed")

    def get_transactions(self):
        return list(self.transactions)

    def eject_card(self):
        self.card_reader.eject_card()
        self.current_card = None
        self.current_account = None
        self.state = ATMState.IDLE

    def _require_authenticated(self):
        if self.state not in (ATMState.AUTHENTICATED, ATMState.TRANSACTION):
            raise ValueError("Authenticate first")

    def _record_transaction(self, transaction_type, amount, description):
        self._transaction_counter += 1
        transaction = Transaction(
            transaction_id=self._transaction_counter,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
        )
        self.transactions.append(transaction)

    @staticmethod
    def _describe_notes(notes):
        return ", ".join(f"{count}x{denomination}" for denomination, count in notes.items())