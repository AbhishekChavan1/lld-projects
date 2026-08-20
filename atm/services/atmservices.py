from .bank import Bank
from ..models.account import Account
from ..models.card import Card
from ..core.atm import ATM


class ATMService:
    def __init__(self):
        self.bank = Bank()

    def create_account(self, account_number, holder_name, balance=0):
        account = Account(account_number, holder_name, balance)
        return account

    def issue_card(self, card_holder, card_number, pin, account):
        card = Card(card_holder, card_number, pin, account)
        self.bank.add_card(card)
        return card

    def create_session(self, card_number):
        atm = ATM(self.bank)
        atm.insert_card(card_number)
        return atm
