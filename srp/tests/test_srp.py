import dataclasses

import pytest

from order_processing import (
    CouponPricingService,
    EmailNotificationService,
    InMemoryOrderRepository,
    NotificationService,
    Order,
    OrderApplicationService,
    OrderRepository,
    OrderValidator,
    PricingService,
)


@pytest.fixture
def repo():
    return InMemoryOrderRepository()


@pytest.fixture
def service(repo):
    return OrderApplicationService(
        validator=OrderValidator(),
        pricing_service=CouponPricingService(),
        repository=repo,
        notification_service=EmailNotificationService(),
    )


class RecordingNotifier(NotificationService):
    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    def send_confirmation(self, user_id: str, order_id: str) -> None:
        self.sent.append((user_id, order_id))


class TestOrder:
    def test_fields_and_default_coupon(self):
        order = Order("ORD-1", "user-1", 100.0)
        assert order.coupon_code is None
        assert (order.id, order.user_id, order.amount) == ("ORD-1", "user-1", 100.0)

    def test_is_immutable(self):
        order = Order("ORD-1", "user-1", 100.0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            order.amount = 5.0

    def test_equality_is_by_value(self):
        assert Order("ORD-1", "u", 10.0) == Order("ORD-1", "u", 10.0)

    def test_hashable_because_frozen(self):
        assert len({Order("ORD-1", "u", 10.0), Order("ORD-1", "u", 10.0)}) == 1


class TestOrderValidator:
    def test_accepts_valid_order(self):
        OrderValidator().validate(Order("ORD-1", "user-1", 10.0))

    def test_rejects_zero_amount(self):
        with pytest.raises(ValueError, match="Amount must be positive"):
            OrderValidator().validate(Order("ORD-1", "user-1", 0.0))

    def test_rejects_negative_amount(self):
        with pytest.raises(ValueError, match="Amount must be positive"):
            OrderValidator().validate(Order("ORD-1", "user-1", -1.0))

    def test_rejects_empty_user_id(self):
        with pytest.raises(ValueError, match="User ID required"):
            OrderValidator().validate(Order("ORD-1", "", 10.0))

    def test_rejects_whitespace_user_id(self):
        with pytest.raises(ValueError, match="User ID required"):
            OrderValidator().validate(Order("ORD-1", "   ", 10.0))

    def test_amount_is_checked_before_user_id(self):
        with pytest.raises(ValueError, match="Amount must be positive"):
            OrderValidator().validate(Order("ORD-1", "", -1.0))

    def test_performs_no_io(self):
        """SRP: the validator's only job is validation."""
        assert [m for m in dir(OrderValidator) if not m.startswith("_")] == ["validate"]


class TestPricingService:
    def test_base_is_abstract(self):
        with pytest.raises(TypeError):
            PricingService()

    def test_applies_ten_percent_coupon(self):
        assert CouponPricingService().apply_discount(
            Order("ORD-1", "u", 250.0, "SAVE10")
        ) == 225.0

    def test_unknown_coupon_leaves_price_untouched(self):
        assert CouponPricingService().apply_discount(
            Order("ORD-1", "u", 250.0, "NOPE")
        ) == 250.0

    def test_missing_coupon_leaves_price_untouched(self):
        assert CouponPricingService().apply_discount(Order("ORD-1", "u", 250.0)) == 250.0

    def test_discount_is_rounded_to_two_places(self):
        assert CouponPricingService().apply_discount(
            Order("ORD-1", "u", 33.33, "SAVE10")
        ) == 30.0

    def test_tiny_order_rounds_discount_up_to_one_cent(self):
        assert CouponPricingService().apply_discount(
            Order("ORD-1", "u", 0.05, "SAVE10")
        ) == 0.04

    def test_result_is_always_rounded_to_cents(self):
        for amount in (0.07, 1.11, 19.99, 123.456):
            result = CouponPricingService().apply_discount(
                Order("ORD-1", "u", amount, "SAVE10")
            )
            assert result == round(result, 2)


class TestInMemoryOrderRepository:
    def test_base_is_abstract(self):
        with pytest.raises(TypeError):
            OrderRepository()

    def test_saves_and_reads_back(self, repo):
        order = Order("ORD-1", "u", 10.0)
        repo.save(order)
        assert repo.get("ORD-1") is order

    def test_missing_order_returns_none(self, repo):
        assert repo.get("nope") is None

    def test_save_overwrites_same_id(self, repo):
        repo.save(Order("ORD-1", "u", 10.0))
        repo.save(Order("ORD-1", "u", 20.0))
        assert repo.get("ORD-1").amount == 20.0


class TestEmailNotificationService:
    def test_base_is_abstract(self):
        with pytest.raises(TypeError):
            NotificationService()

    def test_prints_confirmation(self, capsys):
        EmailNotificationService().send_confirmation("user-42", "ORD-1")
        out = capsys.readouterr().out
        assert "user-42" in out
        assert "ORD-1" in out


class TestOrderApplicationService:
    def test_returns_discounted_amount(self, service):
        assert service.place_order(Order("ORD-1", "user-42", 250.0, "SAVE10")) == 225.0

    def test_persists_the_order(self, service, repo):
        service.place_order(Order("ORD-1", "user-42", 250.0))
        assert repo.get("ORD-1") is not None

    def test_sends_confirmation(self):
        notifier = RecordingNotifier()
        svc = OrderApplicationService(
            OrderValidator(), CouponPricingService(), InMemoryOrderRepository(), notifier
        )
        svc.place_order(Order("ORD-1", "user-42", 250.0))
        assert notifier.sent == [("user-42", "ORD-1")]

    def test_invalid_order_is_not_persisted(self, service, repo):
        with pytest.raises(ValueError):
            service.place_order(Order("ORD-1", "user-42", -5.0))
        assert repo.get("ORD-1") is None

    def test_invalid_order_sends_no_notification(self):
        notifier = RecordingNotifier()
        svc = OrderApplicationService(
            OrderValidator(), CouponPricingService(), InMemoryOrderRepository(), notifier
        )
        with pytest.raises(ValueError):
            svc.place_order(Order("ORD-1", "user-42", -5.0))
        assert notifier.sent == []

    def test_validation_runs_before_pricing(self):
        class ExplodingPricing(PricingService):
            def apply_discount(self, order: Order) -> float:
                raise AssertionError("pricing must not run for invalid orders")

        svc = OrderApplicationService(
            OrderValidator(),
            ExplodingPricing(),
            InMemoryOrderRepository(),
            RecordingNotifier(),
        )
        with pytest.raises(ValueError):
            svc.place_order(Order("ORD-1", "", 10.0))

    def test_step_order_is_validate_price_save_notify(self):
        calls: list[str] = []

        class TrackingPricing(PricingService):
            def apply_discount(self, order: Order) -> float:
                calls.append("price")
                return 1.0

        class TrackingRepo(OrderRepository):
            def save(self, order: Order) -> None:
                calls.append("save")

        class TrackingNotifier(NotificationService):
            def send_confirmation(self, user_id: str, order_id: str) -> None:
                calls.append("notify")

        svc = OrderApplicationService(
            OrderValidator(), TrackingPricing(), TrackingRepo(), TrackingNotifier()
        )
        svc.place_order(Order("ORD-1", "u", 10.0))
        assert calls == ["price", "save", "notify"]


class TestSingleResponsibility:
    """SRP is structural: each collaborator does exactly one job."""

    def test_service_exposes_only_place_order(self):
        public = [m for m in dir(OrderApplicationService) if not m.startswith("_")]
        assert public == ["place_order"]

    def test_each_collaborator_has_a_single_public_method(self):
        assert [m for m in dir(CouponPricingService) if not m.startswith("_")] == [
            "apply_discount"
        ]
        assert [m for m in dir(InMemoryOrderRepository) if not m.startswith("_")] == [
            "get",
            "save",
        ]
        assert [m for m in dir(EmailNotificationService) if not m.startswith("_")] == [
            "send_confirmation"
        ]

    def test_application_service_does_not_contain_payment_branches(self):
        """A new payment type must not require editing the application service."""
        import inspect

        source = inspect.getsource(OrderApplicationService.place_order)
        for banned in ("if ", "elif ", "CARD", "UPI", "PAYPAL"):
            assert banned not in source

    def test_strategies_are_swappable_without_touching_service(self):
        class FlatPricing(PricingService):
            def apply_discount(self, order: Order) -> float:
                return order.amount

        repo = InMemoryOrderRepository()
        svc = OrderApplicationService(
            OrderValidator(), FlatPricing(), repo, RecordingNotifier()
        )
        assert svc.place_order(Order("ORD-1", "u", 250.0, "SAVE10")) == 250.0
