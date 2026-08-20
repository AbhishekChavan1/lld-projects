from ..payments.payment import Payment


class UPIPayment(Payment):
    def process(self) -> bool:
        print(f"  UPI payment processed: ${self.amount:.2f}")
        return True
