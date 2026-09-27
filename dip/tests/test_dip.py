import inspect

import pytest

from booking_service import (
    BookingService,
    FakeNotificationService,
    FakePaymentGateway,
    FakeSeatInventory,
    NotificationPort,
    PaymentPort,
    PostgresSeatInventory,
    RazorpayPaymentGateway,
    SeatInventoryPort,
    StripePaymentGateway,
    TwilioNotificationService,
)


@pytest.fixture
def inventory():
    return FakeSeatInventory()


@pytest.fixture
def payment():
    return FakePaymentGateway()


@pytest.fixture
def notification():
    return FakeNotificationService()


@pytest.fixture
def service(inventory, payment, notification):
    return BookingService(inventory, payment, notification)


class TestPortContracts:
    def test_inventory_port_is_abstract(self):
        with pytest.raises(TypeError):
            SeatInventoryPort()

    def test_payment_port_is_abstract(self):
        with pytest.raises(TypeError):
            PaymentPort()

    def test_notification_port_is_abstract(self):
        with pytest.raises(TypeError):
            NotificationPort()

    def test_adapters_implement_their_port(self):
        assert isinstance(PostgresSeatInventory(), SeatInventoryPort)
        assert isinstance(StripePaymentGateway(), PaymentPort)
        assert isinstance(RazorpayPaymentGateway(), PaymentPort)
        assert isinstance(TwilioNotificationService(), NotificationPort)

    def test_ports_are_defined_in_the_domain_layer(self):
        """Ports live with the use case, not next to the vendors."""
        source = inspect.getsource(BookingService)
        for vendor in ("Stripe", "Razorpay", "Postgres", "Twilio"):
            assert vendor not in source


class TestHappyPath:
    def test_returns_true(self, service):
        assert service.book_ticket("user-42", "A12", 250.0) is True

    def test_notifies_with_seat_reference(self, service, notification):
        service.book_ticket("user-42", "A12", 250.0)
        assert notification.sent == [
            ("user-42", "Booking confirmed for seat A12")
        ]

    def test_does_not_release_a_reserved_seat(self, service, inventory):
        service.book_ticket("user-42", "A12", 250.0)
        assert inventory.released == []

    def test_prints_progress(self, service, capsys):
        service.book_ticket("user-42", "A12", 250.0)
        out = capsys.readouterr().out
        assert "[Booking] Success: A12" in out

    def test_zero_price_booking_succeeds(self, service, notification):
        assert service.book_ticket("user-42", "FREE", 0.0) is True
        assert len(notification.sent) == 1


class TestReservationFailure:
    def test_returns_false(self, service, inventory):
        inventory.fail_on_reserve = True
        assert service.book_ticket("user-42", "A12", 250.0) is False

    def test_payment_is_not_attempted(self, service, payment, inventory):
        class ExplodingPayment(PaymentPort):
            def charge(self, user_id: str, amount: float) -> bool:
                raise AssertionError("must not charge when the seat is gone")

            def refund(self, transaction_id: str) -> None:
                raise AssertionError("must not refund")

        svc = BookingService(
            FakeSeatInventory(fail_on_reserve=True), ExplodingPayment(), FakeNotificationService()
        )
        assert svc.book_ticket("user-42", "A12", 250.0) is False

    def test_no_notification_is_sent(self, service, notification, inventory):
        inventory.fail_on_reserve = True
        service.book_ticket("user-42", "A12", 250.0)
        assert notification.sent == []

    def test_reports_the_failure(self, service, inventory, capsys):
        inventory.fail_on_reserve = True
        service.book_ticket("user-42", "A12", 250.0)
        assert "Reservation failed: A12" in capsys.readouterr().out


class TestPaymentFailure:
    def test_returns_false(self, service, payment):
        payment.should_succeed = False
        assert service.book_ticket("user-42", "A12", 250.0) is False

    def test_releases_the_seat(self, service, payment, inventory):
        payment.should_succeed = False
        service.book_ticket("user-42", "A12", 250.0)
        assert inventory.released == ["A12"]

    def test_sends_no_notification(self, service, payment, notification):
        payment.should_succeed = False
        service.book_ticket("user-42", "A12", 250.0)
        assert notification.sent == []

    def test_reports_the_failure(self, service, payment, capsys):
        payment.should_succeed = False
        service.book_ticket("user-42", "A12", 250.0)
        assert "Payment failed, released seat" in capsys.readouterr().out


class TestDependencyInversion:
    def test_swapping_the_gateway_needs_no_service_change(self, capsys):
        inventory = PostgresSeatInventory()
        for gateway in (StripePaymentGateway(), RazorpayPaymentGateway()):
            svc = BookingService(inventory, gateway, TwilioNotificationService())
            assert svc.book_ticket("user-42", "A12", 250.0) is True
        out = capsys.readouterr().out
        assert "[Stripe] Charged 250.0 for user-42" in out
        assert "[Razorpay] Charged 250.0 for user-42" in out

    def test_service_constructor_signature_is_vendor_free(self):
        params = list(inspect.signature(BookingService.__init__).parameters)
        assert params == ["self", "inventory", "payment", "notification"]

    def test_service_never_imports_a_vendor(self):
        source = inspect.getsource(BookingService)
        for banned in ("import Stripe", "import Razorpay", "Postgres", "Twilio"):
            assert banned not in source

    def test_logic_is_testable_without_infrastructure(self):
        inv = FakeSeatInventory()
        pay = FakePaymentGateway(should_succeed=False)
        notif = FakeNotificationService()
        result = BookingService(inv, pay, notif).book_ticket("u1", "Z9", 100.0)
        assert result is False
        assert inv.released == ["Z9"]
        assert notif.sent == []

    def test_a_brand_new_gateway_needs_no_registration(self, capsys):
        class PayPalGateway(PaymentPort):
            def charge(self, user_id: str, amount: float) -> bool:
                print(f"[PayPal] Charged {amount}")
                return True

            def refund(self, transaction_id: str) -> None:
                print(f"[PayPal] Refunded {transaction_id}")

        svc = BookingService(
            FakeSeatInventory(), PayPalGateway(), FakeNotificationService()
        )
        assert svc.book_ticket("user-42", "A12", 250.0) is True
        assert "[PayPal] Charged 250.0" in capsys.readouterr().out

    def test_production_adapters_print_expected_lines(self, capsys):
        PostgresSeatInventory().reserve("A12", "user-42")
        PostgresSeatInventory().release("A12")
        StripePaymentGateway().refund("tx-1")
        TwilioNotificationService().send("user-42", "hi")
        out = capsys.readouterr().out
        assert "[Postgres] Reserved seat=A12 user=user-42" in out
        assert "[Postgres] Released seat=A12" in out
        assert "[Stripe] Refunded tx-1" in out
        assert "[Twilio] SMS to user-42: hi" in out

    def test_fakes_are_the_default_in_main(self):
        """The demo proves the design: real adapters need no fakes at all."""
        assert FakeSeatInventory().reserve("A", "u") is True
        assert FakePaymentGateway().charge("u", 1.0) is True
        assert FakeSeatInventory(fail_on_reserve=True).reserve("A", "u") is False
        assert FakePaymentGateway(should_succeed=False).charge("u", 1.0) is False
