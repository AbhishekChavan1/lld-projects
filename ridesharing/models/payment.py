from enums.paymentstatus import PaymentStatus


class Payment:
    def __init__(self, payment_id: str, amount: float, status: PaymentStatus) -> None:
        self.payment_id = payment_id
        self.amount = amount
        self.status = status

    def update_status(self, new_status: PaymentStatus) -> None:
        self.status = new_status

    def successful_payment(self) -> bool:
        return self.status == PaymentStatus.COMPLETED

    def failed_payment(self) -> bool:
        return self.status == PaymentStatus.FAILED
