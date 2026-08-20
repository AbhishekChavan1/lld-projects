import pytest

from core.atm import ATM, ATMState
from services.atmservices import ATMService


@pytest.fixture
def service():
    return ATMService()


@pytest.fixture
def atm(service):
    account = service.create_account("AC1001", "Alice", balance=5000)
    service.issue_card("Alice", "4000000000000001", "1234", account)
    atm = service.create_session("4000000000000001")
    atm.authenticate("1234")
    return atm


def test_insert_invalid_card(service):
    with pytest.raises(ValueError):
        service.create_session("9999999999999999")


def test_wrong_pin_then_block(service):
    account = service.create_account("AC1002", "Bob", balance=1000)
    service.issue_card("Bob", "4000000000000002", "4321", account)

    card = service.bank.get_card("4000000000000002")
    for attempt in range(ATM.MAX_PIN_ATTEMPTS):
        atm = service.create_session("4000000000000002")
        message = "Incorrect PIN" if attempt < ATM.MAX_PIN_ATTEMPTS - 1 else "Card blocked"
        with pytest.raises(ValueError, match=message):
            atm.authenticate("0000")

    assert card.is_blocked
    with pytest.raises(ValueError, match="Card is blocked"):
        service.create_session("4000000000000002")


def test_check_balance(atm):
    assert atm.check_balance() == 5000


def test_withdraw(atm):
    notes = atm.withdraw(1350)
    assert sum(d * c for d, c in notes.items()) == 1350
    assert atm.check_balance() == 3650


def test_withdraw_insufficient_balance(atm):
    with pytest.raises(ValueError, match="Insufficient balance"):
        atm.withdraw(100000)


def test_withdraw_unavailable_amount(atm):
    with pytest.raises(ValueError, match="Cannot dispense"):
        atm.withdraw(5)


def test_deposit(atm):
    atm.deposit(500)
    assert atm.check_balance() == 5500


def test_change_pin(atm):
    atm.change_pin("1234", "5678")
    assert atm.current_card.validate_pin("5678")
    with pytest.raises(ValueError):
        atm.change_pin("1234", "0000")


def test_transactions_recorded(atm):
    atm.withdraw(1000)
    atm.deposit(200)
    types = [t.transaction_type.value for t in atm.get_transactions()]
    assert types == ["withdrawal", "deposit"]


def test_eject_returns_to_idle(atm):
    atm.eject_card()
    assert atm.state == ATMState.IDLE
    with pytest.raises(ValueError, match="Authenticate first"):
        atm.check_balance()
