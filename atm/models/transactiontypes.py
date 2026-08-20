from enum import Enum

class TransactionType(Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    BALANCE_INQUIRY = "balance_inquiry"
    PIN_CHANGE = "pin_change"