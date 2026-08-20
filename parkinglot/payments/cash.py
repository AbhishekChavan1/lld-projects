from ..payments.payment import Payment


class CashPayment(Payment):
    def process(self) -> bool:
        print(f"  Cash payment processed: ${self.amount:.2f}")
        return True
