from abc import ABC, abstractmethod


class SeatInventoryPort(ABC):
    @abstractmethod
    def reserve(self, seat_id: str, user_id: str) -> bool:
        pass

    @abstractmethod
    def release(self, seat_id: str) -> None:
        pass


class PaymentPort(ABC):
    @abstractmethod
    def charge(self, user_id: str, amount: float) -> bool:
        pass

    @abstractmethod
    def refund(self, transaction_id: str) -> None:
        pass


class NotificationPort(ABC):
    @abstractmethod
    def send(self, user_id: str, message: str) -> None:
        pass


class BookingService:
    def __init__(
        self,
        inventory: SeatInventoryPort,
        payment: PaymentPort,
        notification: NotificationPort,
    ):
        self._inventory = inventory
        self._payment = payment
        self._notification = notification

    def book_ticket(self, user_id: str, seat_id: str, price: float) -> bool:
        if not self._inventory.reserve(seat_id, user_id):
            print(f"[Booking] Reservation failed: {seat_id}")
            return False
        if not self._payment.charge(user_id, price):
            self._inventory.release(seat_id)
            print("[Booking] Payment failed, released seat")
            return False
        self._notification.send(user_id, f"Booking confirmed for seat {seat_id}")
        print(f"[Booking] Success: {seat_id}")
        return True


class PostgresSeatInventory(SeatInventoryPort):
    def reserve(self, seat_id: str, user_id: str) -> bool:
        print(f"[Postgres] Reserved seat={seat_id} user={user_id}")
        return True

    def release(self, seat_id: str) -> None:
        print(f"[Postgres] Released seat={seat_id}")


class StripePaymentGateway(PaymentPort):
    def charge(self, user_id: str, amount: float) -> bool:
        print(f"[Stripe] Charged {amount} for {user_id}")
        return True

    def refund(self, transaction_id: str) -> None:
        print(f"[Stripe] Refunded {transaction_id}")


class RazorpayPaymentGateway(PaymentPort):
    def charge(self, user_id: str, amount: float) -> bool:
        print(f"[Razorpay] Charged {amount} for {user_id}")
        return True

    def refund(self, transaction_id: str) -> None:
        print(f"[Razorpay] Refunded {transaction_id}")


class TwilioNotificationService(NotificationPort):
    def send(self, user_id: str, message: str) -> None:
        print(f"[Twilio] SMS to {user_id}: {message}")


class FakeSeatInventory(SeatInventoryPort):
    """Test double: no database needed to test booking logic."""

    def __init__(self, fail_on_reserve: bool = False):
        self.fail_on_reserve = fail_on_reserve
        self.released: list[str] = []

    def reserve(self, seat_id: str, user_id: str) -> bool:
        return not self.fail_on_reserve

    def release(self, seat_id: str) -> None:
        self.released.append(seat_id)


class FakePaymentGateway(PaymentPort):
    def __init__(self, should_succeed: bool = True):
        self.should_succeed = should_succeed

    def charge(self, user_id: str, amount: float) -> bool:
        return self.should_succeed

    def refund(self, transaction_id: str) -> None:
        pass


class FakeNotificationService(NotificationPort):
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send(self, user_id: str, message: str) -> None:
        self.sent.append((user_id, message))


def main():
    inventory = PostgresSeatInventory()

    stripe_booking = BookingService(inventory, StripePaymentGateway(), TwilioNotificationService())
    stripe_booking.book_ticket("user-42", "A12", 250.0)

    print("\nSwap Stripe -> Razorpay; BookingService untouched:")
    razorpay_booking = BookingService(inventory, RazorpayPaymentGateway(), TwilioNotificationService())
    razorpay_booking.book_ticket("user-42", "B7", 250.0)

    print("\nUnit-test booking logic with fakes (payment declines):")
    inv = FakeSeatInventory()
    pay = FakePaymentGateway(should_succeed=False)
    notif = FakeNotificationService()
    result = BookingService(inv, pay, notif).book_ticket("u1", "Z9", 100.0)
    assert not result
    assert inv.released == ["Z9"]
    assert not notif.sent
    print("[Test] Seat released after failed payment, no notification sent")


if __name__ == "__main__":
    main()
