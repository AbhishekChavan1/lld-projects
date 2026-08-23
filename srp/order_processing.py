from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    id: str
    user_id: str
    amount: float
    coupon_code: str | None = None


class OrderValidator:
    def validate(self, order: Order) -> None:
        if order.amount <= 0:
            raise ValueError("Amount must be positive")
        if not order.user_id or not order.user_id.strip():
            raise ValueError("User ID required")


class PricingService(ABC):
    @abstractmethod
    def apply_discount(self, order: Order) -> float:
        pass


class CouponPricingService(PricingService):
    def apply_discount(self, order: Order) -> float:
        discount = 0.0
        if order.coupon_code == "SAVE10":
            discount = round(order.amount * 0.10, 2)
        final_amount = round(order.amount - discount, 2)
        return final_amount


class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> None:
        pass


class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._orders: dict[str, Order] = {}

    def save(self, order: Order) -> None:
        self._orders[order.id] = order

    def get(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)


class NotificationService(ABC):
    @abstractmethod
    def send_confirmation(self, user_id: str, order_id: str) -> None:
        pass


class EmailNotificationService(NotificationService):
    def send_confirmation(self, user_id: str, order_id: str) -> None:
        print(f"[Notification] Confirmation sent to user {user_id} for order {order_id}")


class OrderApplicationService:
    def __init__(
        self,
        validator: OrderValidator,
        pricing_service: PricingService,
        repository: OrderRepository,
        notification_service: NotificationService,
    ):
        self._validator = validator
        self._pricing_service = pricing_service
        self._repository = repository
        self._notification_service = notification_service

    def place_order(self, order: Order) -> float:
        self._validator.validate(order)
        final_amount = self._pricing_service.apply_discount(order)
        self._repository.save(order)
        self._notification_service.send_confirmation(order.user_id, order.id)
        return final_amount


def main():
    app = OrderApplicationService(
        validator=OrderValidator(),
        pricing_service=CouponPricingService(),
        repository=InMemoryOrderRepository(),
        notification_service=EmailNotificationService(),
    )

    order = Order("ORD-001", "user-42", 250.0, "SAVE10")
    final_amount = app.place_order(order)
    print(f"[Main] Order placed. Final amount: {final_amount}")

    try:
        app.place_order(Order("ORD-002", "", -10.0))
    except ValueError as e:
        print(f"[Main] Rejected invalid order: {e}")


if __name__ == "__main__":
    main()
