from ..payments.payment import Payment


class CardPayment(Payment):
    def process(self) -> bool:
        print(f"  Card payment processed: ${self.amount:.2f}")
        return True
