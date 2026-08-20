from datetime import datetime

class Transaction:
    def __init__(self, transaction_id, amount, transaction_type, description="", currency="INR", timestamp=None):
        self.transaction_id = transaction_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.description = description
        self.currency = currency
        self.timestamp = timestamp if timestamp else datetime.now()

    def __repr__(self):
        return (
            f"Transaction(transaction_id={self.transaction_id}, "
            f"amount={self.amount}, type='{self.transaction_type.value}', "
            f"currency='{self.currency}', timestamp={self.timestamp})"
        )

    