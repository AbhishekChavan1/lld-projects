from ..enums.payment import PaymentType
from .payment import Payment
from .cash import CashPayment
from .card import CardPayment
from .upi import UPIPayment


class PaymentFactory:
    @staticmethod
    def create_payment(payment_type: PaymentType, amount: float) -> Payment:
        mapping = {
            PaymentType.CASH: CashPayment,
            PaymentType.CARD: CardPayment,
            PaymentType.UPI: UPIPayment,
        }
        cls = mapping.get(payment_type)
        if cls is None:
            raise ValueError(f"Unsupported payment type: {payment_type}")
        return cls(amount)
