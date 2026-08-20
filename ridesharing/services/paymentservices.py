from enums.paymentstatus import PaymentStatus
from models.payment import Payment
from models.rider import Rider


class PaymentService:
    """Handles payments using the rider's wallet balance."""

    def __init__(self) -> None:
        self.payment_counter = 0

    def process_payment(self, rider: Rider, amount: float) -> Payment:
        """Debit the rider's wallet and return the payment record."""
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        self.payment_counter += 1
        payment = Payment(
            payment_id=f"PAY-{self.payment_counter:04d}",
            amount=amount,
            status=PaymentStatus.PENDING,
        )

        if rider.wallet_balance < amount:
            payment.update_status(PaymentStatus.FAILED)
            return payment

        rider.wallet_balance -= amount
        payment.update_status(PaymentStatus.COMPLETED)
        return payment
