"""Tests for the Adapter Pattern (structural)."""
import inspect

import pytest

from adapter.acquirer_sdk import AcquirerError, ModernAcquirerSdk
from adapter.class_adapter import PayPalClassAdapter
from adapter.leaky_client import LegacyCheckoutService
from adapter.legacy_paypal_sdk import LegacyPayPalSdk, LegacySdkError
from adapter.notification_sdks import LegacySmsSdk, SmsDeliveryError, SmtpRelay
from adapter.payment_adapters import (
    AcquirerAdapter,
    InHouseLedgerGateway,
    PayPalAdapter,
    SmtpEmailSenderAdapter,
    SmsSenderAdapter,
)
from adapter.ports import (
    NotificationChannel,
    NotificationResult,
    NotificationSender,
    PaymentGateway,
    PaymentResult,
    PaymentStatus,
)
from adapter.registry import CheckoutService, GatewayRegistry

VENDOR_TOKENS = (
    "paypal",
    "acquirer",
    "PPTXN",
    "acq_",
    "charge_cents",
    "create_payment",
    "LegacySdkError",
    "AcquirerError",
    "MINOR_UNITS_PER_MAJOR",
)


@pytest.fixture
def paypal_sdk() -> LegacyPayPalSdk:
    return LegacyPayPalSdk("client-id", "secret")


@pytest.fixture
def paypal(paypal_sdk: LegacyPayPalSdk) -> PayPalAdapter:
    return PayPalAdapter(paypal_sdk)


@pytest.fixture
def acquirer_sdk() -> ModernAcquirerSdk:
    return ModernAcquirerSdk("api-key")


@pytest.fixture
def acquirer(acquirer_sdk: ModernAcquirerSdk) -> AcquirerAdapter:
    return AcquirerAdapter(acquirer_sdk)


@pytest.fixture
def sms_sender() -> SmsSenderAdapter:
    return SmsSenderAdapter(LegacySmsSdk("sid", "token"), sender_id="SHOPT")


@pytest.fixture
def email_sender() -> SmtpEmailSenderAdapter:
    return SmtpEmailSenderAdapter(SmtpRelay("relay.local"), "no-reply@shop.io")


class TestPorts:
    """The target interfaces are the application's own vocabulary."""

    def test_payment_gateway_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            PaymentGateway()

    def test_notification_sender_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            NotificationSender()

    def test_payment_result_is_approved_only_for_approved(self):
        approved = PaymentResult("t1", PaymentStatus.APPROVED, 10.0, "USD")
        declined = PaymentResult("t2", PaymentStatus.DECLINED, 10.0, "USD")
        assert approved.is_approved
        assert not declined.is_approved

    def test_payment_result_defaults_optional_fields_to_none(self):
        result = PaymentResult("t1", PaymentStatus.APPROVED, 10.0, "USD")
        assert result.vendor_reference is None
        assert result.reason is None

    def test_payment_result_is_immutable(self):
        result = PaymentResult("t1", PaymentStatus.APPROVED, 10.0, "USD")
        with pytest.raises(Exception):
            result.status = PaymentStatus.ERROR

    def test_payment_result_repr_shows_amount_and_currency(self):
        result = PaymentResult("t1", PaymentStatus.APPROVED, 12.5, "USD")
        assert "12.50 USD" in repr(result)
        assert "approved" in repr(result)

    def test_notification_result_repr_shows_channel(self):
        result = NotificationResult(NotificationChannel.SMS, "SM1", True)
        assert "sms" in repr(result)

    def test_status_enum_values_are_lowercase_strings(self):
        assert PaymentStatus.APPROVED.value == "approved"
        assert NotificationChannel.EMAIL.value == "email"


class TestLegacyPayPalSdk:
    """The adaptee is fixed third-party code: awkward on purpose."""

    def test_charge_before_authentication_raises(self, paypal_sdk):
        with pytest.raises(LegacySdkError, match="Not authenticated"):
            paypal_sdk.charge_cents(1000, "USD")

    def test_refund_before_authentication_raises(self, paypal_sdk):
        with pytest.raises(LegacySdkError, match="Not authenticated"):
            paypal_sdk.revert("PPTXN-0001")

    def test_authentication_requires_credentials(self):
        sdk = LegacyPayPalSdk("", "secret")
        with pytest.raises(LegacySdkError, match="Missing client credentials"):
            sdk.authenticate()

    def test_authentication_sets_flag(self, paypal_sdk):
        assert not paypal_sdk.is_authenticated()
        assert paypal_sdk.authenticate()
        assert paypal_sdk.is_authenticated()

    def test_charge_returns_dict_with_completed_state(self, paypal_sdk):
        paypal_sdk.authenticate()
        raw = paypal_sdk.charge_cents(1000, "USD")
        assert raw["state"] == "COMPLETED"
        assert raw["err"] is None
        assert raw["id"].startswith("PPTXN-")

    def test_charge_rejects_unsupported_currency(self, paypal_sdk):
        paypal_sdk.authenticate()
        with pytest.raises(LegacySdkError, match="Unsupported currency"):
            paypal_sdk.charge_cents(1000, "JPY")

    def test_charge_rejects_non_positive_amount(self, paypal_sdk):
        paypal_sdk.authenticate()
        with pytest.raises(LegacySdkError, match="must be positive"):
            paypal_sdk.charge_cents(0, "USD")

    def test_charge_declines_above_risk_limit(self, paypal_sdk):
        paypal_sdk.authenticate()
        raw = paypal_sdk.charge_cents(100_001, "USD")
        assert raw["state"] == "DECLINED"
        assert raw["err"] == "RISK_LIMIT_EXCEEDED"

    def test_charge_allows_exactly_the_risk_limit(self, paypal_sdk):
        paypal_sdk.authenticate()
        raw = paypal_sdk.charge_cents(100_000, "USD")
        assert raw["state"] == "COMPLETED"

    def test_revert_returns_refunded_state(self, paypal_sdk):
        paypal_sdk.authenticate()
        raw = paypal_sdk.revert("PPTXN-0001")
        assert raw["state"] == "REFUNDED"
        assert raw["id"] == "PPREF-PPTXN-0001"

    def test_revert_rejects_foreign_id(self, paypal_sdk):
        paypal_sdk.authenticate()
        with pytest.raises(LegacySdkError, match="Unknown charge id"):
            paypal_sdk.revert("acq_00001")

    def test_charge_ids_increment(self, paypal_sdk):
        paypal_sdk.authenticate()
        first = paypal_sdk.charge_cents(100, "USD")["id"]
        second = paypal_sdk.charge_cents(100, "USD")["id"]
        assert first == "PPTXN-0001"
        assert second == "PPTXN-0002"
        assert paypal_sdk.get_charge_count() == 2

    def test_eur_is_supported(self, paypal_sdk):
        paypal_sdk.authenticate()
        assert paypal_sdk.charge_cents(1000, "EUR")["state"] == "COMPLETED"


class TestModernAcquirerSdk:
    """A second vendor with the opposite error convention."""

    def test_missing_api_key_raises(self):
        with pytest.raises(AcquirerError, match="API key is required"):
            ModernAcquirerSdk("")

    def test_api_key_error_carries_machine_code(self):
        with pytest.raises(AcquirerError) as excinfo:
            ModernAcquirerSdk("")
        assert excinfo.value.code == "auth_error"

    def test_create_payment_succeeds_below_tier(self, acquirer_sdk):
        raw = acquirer_sdk.create_payment(4250, "usd")
        assert raw["status"] == "succeeded"
        assert raw["failure_reason"] is None
        assert raw["payment_id"] == "acq_00001"

    def test_create_payment_fails_at_tier(self, acquirer_sdk):
        raw = acquirer_sdk.create_payment(50_000, "usd")
        assert raw["status"] == "failed"
        assert raw["failure_reason"] == "amount_exceeds_merchant_tier"

    def test_create_payment_allows_just_below_tier(self, acquirer_sdk):
        assert acquirer_sdk.create_payment(49_999, "usd")["status"] == "succeeded"

    def test_transport_failure_raises_not_returns(self, acquirer_sdk):
        acquirer_sdk.transport_ok = False
        with pytest.raises(AcquirerError, match="Connection reset"):
            acquirer_sdk.create_payment(100, "usd")

    def test_non_positive_amount_raises(self, acquirer_sdk):
        with pytest.raises(AcquirerError, match="must be positive"):
            acquirer_sdk.create_payment(0, "usd")

    def test_metadata_is_echoed_back(self, acquirer_sdk):
        raw = acquirer_sdk.create_payment(100, "usd", metadata={"ref": "order-1"})
        assert raw["metadata"] == {"ref": "order-1"}

    def test_refund_returns_refund_id(self, acquirer_sdk):
        raw = acquirer_sdk.refund_payment("acq_00001")
        assert raw["refund_id"] == "re_acq_00001"
        assert raw["status"] == "refunded"

    def test_refund_accepts_partial_amount(self, acquirer_sdk):
        raw = acquirer_sdk.refund_payment("acq_00001", amount_minor=500)
        assert raw["amount_minor"] == 500

    def test_refund_rejects_foreign_id(self, acquirer_sdk):
        with pytest.raises(AcquirerError, match="Unknown payment id"):
            acquirer_sdk.refund_payment("PPTXN-0001")

    def test_refund_transport_failure_raises(self, acquirer_sdk):
        acquirer_sdk.transport_ok = False
        with pytest.raises(AcquirerError, match="Connection reset"):
            acquirer_sdk.refund_payment("acq_00001")


class TestNotificationSdks:
    """Two notification vendors with incompatible conventions."""

    def test_sms_requires_credentials(self):
        with pytest.raises(SmsDeliveryError, match="Missing SMS credentials"):
            LegacySmsSdk("", "token")

    def test_sms_rejects_non_e164_number(self):
        sdk = LegacySmsSdk("sid", "token")
        with pytest.raises(SmsDeliveryError, match="Not an E.164 number"):
            sdk.send_text("9876543210", "hello")

    def test_sms_rejects_empty_body(self):
        sdk = LegacySmsSdk("sid", "token")
        with pytest.raises(SmsDeliveryError, match="body cannot be empty"):
            sdk.send_text("+919876543210", "")

    def test_sms_queues_valid_message(self):
        sdk = LegacySmsSdk("sid", "token")
        raw = sdk.send_text("+919876543210", "hello")
        assert raw["status"] == "queued"
        assert raw["sid"] == "SM00000001"

    def test_sms_uses_account_sid_when_no_sender_id(self):
        sdk = LegacySmsSdk("sid", "token")
        assert sdk.send_text("+919876543210", "hi")["sender"] == "sid"

    def test_sms_fails_message_over_segment_cap(self):
        sdk = LegacySmsSdk("sid", "token")
        raw = sdk.send_text("+919876543210", "x" * 481)
        assert raw["status"] == "failed"
        assert raw["error"] == "MESSAGE_TOO_LONG"

    def test_sms_accepts_message_at_segment_cap(self):
        sdk = LegacySmsSdk("sid", "token")
        assert sdk.send_text("+919876543210", "x" * 480)["status"] == "queued"

    def test_relay_returns_zero_on_success(self):
        relay = SmtpRelay("relay.local", "no-reply@shop.io")
        assert relay.deliver(["a@b.com"], "Your order", "shipped") == 0

    def test_relay_returns_250_without_sender(self):
        relay = SmtpRelay("relay.local")
        assert relay.deliver(["a@b.com"], "Your order", "shipped") == 250

    def test_relay_returns_513_for_bad_recipient(self):
        relay = SmtpRelay("relay.local", "no-reply@shop.io")
        assert relay.deliver(["not-an-email"], "Your order", "shipped") == 513

    def test_relay_returns_513_for_empty_recipient_list(self):
        relay = SmtpRelay("relay.local", "no-reply@shop.io")
        assert relay.deliver([], "Your order", "shipped") == 513

    def test_relay_returns_554_for_short_subject(self):
        relay = SmtpRelay("relay.local", "no-reply@shop.io")
        assert relay.deliver(["a@b.com"], "Hi", "shipped") == 554

    def test_relay_set_sender_enables_delivery(self):
        relay = SmtpRelay("relay.local")
        assert relay.deliver(["a@b.com"], "Your order", "shipped") == 250
        relay.set_sender("no-reply@shop.io")
        assert relay.deliver(["a@b.com"], "Your order", "shipped") == 0

    def test_relay_counts_deliveries(self):
        relay = SmtpRelay("relay.local", "no-reply@shop.io")
        relay.deliver(["a@b.com"], "Your order", "shipped")
        assert relay.get_delivery_count() == 1


class TestPayPalAdapter:
    """Translation: major units -> cents, dict -> dataclass, code -> enum."""

    def test_is_a_payment_gateway(self, paypal):
        assert isinstance(paypal, PaymentGateway)

    def test_authenticates_lazily_on_first_charge(self, paypal, paypal_sdk):
        assert paypal_sdk.calls == []
        paypal.charge(10.00)
        assert paypal_sdk.calls[0] == "authenticate"

    def test_authenticates_only_once(self, paypal, paypal_sdk):
        paypal.charge(10.00)
        paypal.charge(10.00)
        assert paypal_sdk.calls.count("authenticate") == 1

    def test_converts_major_units_to_integer_cents(self, paypal, paypal_sdk):
        paypal.charge(42.50)
        assert paypal_sdk.calls[-1] == "charge_cents:4250:USD"

    def test_conversion_rounds_to_nearest_minor_unit(self, paypal, paypal_sdk):
        paypal.charge(10.10)
        assert paypal_sdk.calls[-1] == "charge_cents:1010:USD"

    def test_approved_charge_returns_canonical_result(self, paypal):
        result = paypal.charge(42.50, "USD", "order-1")
        assert result.status is PaymentStatus.APPROVED
        assert result.is_approved
        assert result.transaction_id == "PPTXN-0001"
        assert result.amount == 42.50
        assert result.reason is None

    def test_vendor_reference_is_preserved_for_refunds(self, paypal):
        result = paypal.charge(42.50)
        assert result.vendor_reference == result.transaction_id

    def test_reference_is_forwarded_as_vendor_note(self, paypal, paypal_sdk):
        paypal.charge(42.50, "USD", "order-7")
        paypal.charge(1.00, "USD", "order-8")
        assert paypal_sdk.calls[-1] == "charge_cents:100:USD"

    def test_decline_maps_to_declined_status(self, paypal):
        result = paypal.charge(5000.00)
        assert result.status is PaymentStatus.DECLINED
        assert not result.is_approved

    def test_decline_carries_vendor_reason(self, paypal):
        assert paypal.charge(5000.00).reason == "RISK_LIMIT_EXCEEDED"

    def test_risk_limit_boundary_is_inclusive(self, paypal):
        assert paypal.charge(1000.00).status is PaymentStatus.APPROVED
        assert paypal.charge(1000.01).status is PaymentStatus.DECLINED

    def test_unsupported_currency_becomes_error(self, paypal):
        result = paypal.charge(10.00, "JPY")
        assert result.status is PaymentStatus.ERROR
        assert "Unsupported currency" in result.reason

    def test_zero_amount_is_rejected_without_calling_sdk(self, paypal, paypal_sdk):
        result = paypal.charge(0.0)
        assert result.status is PaymentStatus.ERROR
        assert paypal_sdk.get_charge_count() == 0

    def test_negative_amount_is_rejected(self, paypal):
        assert paypal.charge(-5.00).status is PaymentStatus.ERROR

    def test_sub_minor_amount_becomes_error(self, paypal):
        assert paypal.charge(0.001).status is PaymentStatus.ERROR

    def test_refund_returns_approved_result(self, paypal):
        charge = paypal.charge(10.00)
        refund = paypal.refund(charge.transaction_id)
        assert refund.status is PaymentStatus.APPROVED
        assert refund.transaction_id == "PPREF-PPTXN-0001"

    def test_refund_keeps_original_id_as_vendor_reference(self, paypal):
        charge = paypal.charge(10.00)
        assert paypal.refund(charge.transaction_id).vendor_reference == charge.transaction_id

    def test_refund_of_unknown_id_becomes_error(self, paypal):
        result = paypal.refund("acq_00001")
        assert result.status is PaymentStatus.ERROR
        assert "Unknown charge id" in result.reason

    def test_refund_before_any_charge_works(self, paypal):
        assert paypal.refund("PPTXN-0001").status is PaymentStatus.APPROVED

    def test_provider_name_is_reported(self, paypal):
        assert paypal.get_provider_name() == "paypal"

    def test_repr_mentions_provider(self, paypal):
        assert "paypal" in repr(paypal)


class TestAcquirerAdapter:
    """Translation: exceptions -> PaymentStatus.ERROR instead of a raise."""

    def test_is_a_payment_gateway(self, acquirer):
        assert isinstance(acquirer, PaymentGateway)

    def test_converts_major_units_to_minor_units(self, acquirer, acquirer_sdk):
        acquirer.charge(42.50)
        assert acquirer_sdk.calls[-1] == "create_payment:4250:usd"

    def test_lowercases_currency_for_the_vendor(self, acquirer, acquirer_sdk):
        acquirer.charge(10.00, "EUR")
        assert acquirer_sdk.calls[-1] == "create_payment:1000:eur"

    def test_result_currency_is_canonical_upper_case(self, acquirer):
        assert acquirer.charge(10.00, "eur").currency == "EUR"

    def test_approved_charge_returns_canonical_result(self, acquirer):
        result = acquirer.charge(42.50)
        assert result.status is PaymentStatus.APPROVED
        assert result.transaction_id == "acq_00001"

    def test_reference_is_sent_as_metadata(self, acquirer, acquirer_sdk):
        acquirer.charge(42.50, "USD", "order-9")
        assert acquirer.charge(1.00, "USD", "order-10")
        assert acquirer_sdk.get_payment_count() == 2

    def test_decline_maps_to_declined_status(self, acquirer):
        result = acquirer.charge(600.00)
        assert result.status is PaymentStatus.DECLINED
        assert result.reason == "amount_exceeds_merchant_tier"

    def test_tier_boundary_is_inclusive(self, acquirer):
        assert acquirer.charge(499.99).status is PaymentStatus.APPROVED
        assert acquirer.charge(500.00).status is PaymentStatus.DECLINED

    def test_transport_failure_is_converted_to_error(self, acquirer, acquirer_sdk):
        acquirer_sdk.transport_ok = False
        result = acquirer.charge(42.50)
        assert result.status is PaymentStatus.ERROR
        assert result.reason.startswith("transport_error:")

    def test_sdk_exception_never_reaches_the_caller(self, acquirer, acquirer_sdk):
        acquirer_sdk.transport_ok = False
        acquirer.charge(42.50)  # must not raise

    def test_zero_amount_is_rejected_without_calling_sdk(self, acquirer, acquirer_sdk):
        assert acquirer.charge(0.0).status is PaymentStatus.ERROR
        assert acquirer_sdk.get_payment_count() == 0

    def test_refund_returns_approved_result(self, acquirer):
        charge = acquirer.charge(10.00)
        refund = acquirer.refund(charge.transaction_id)
        assert refund.status is PaymentStatus.APPROVED
        assert refund.transaction_id == "re_acq_00001"

    def test_refund_keeps_payment_id_as_vendor_reference(self, acquirer):
        charge = acquirer.charge(10.00)
        assert acquirer.refund(charge.transaction_id).vendor_reference == "acq_00001"

    def test_refund_of_unknown_id_becomes_error(self, acquirer):
        result = acquirer.refund("PPTXN-0001")
        assert result.status is PaymentStatus.ERROR
        assert "not_found" in result.reason

    def test_provider_name_is_reported(self, acquirer):
        assert acquirer.get_provider_name() == "acquirer"


class TestSharedGatewayContract:
    """Both adapters honour one contract, which is the point of the pattern."""

    @pytest.fixture(params=["paypal", "acquirer", "inhouse"])
    def gateway(self, request):
        if request.param == "paypal":
            return PayPalAdapter(LegacyPayPalSdk("client-id", "secret"))
        if request.param == "acquirer":
            return AcquirerAdapter(ModernAcquirerSdk("api-key"))
        return InHouseLedgerGateway()

    def test_satisfies_the_abstract_interface(self, gateway):
        assert isinstance(gateway, PaymentGateway)

    def test_approves_a_normal_charge(self, gateway):
        result = gateway.charge(42.50)
        assert result.status is PaymentStatus.APPROVED
        assert result.transaction_id

    def test_returns_major_units_unchanged(self, gateway):
        assert gateway.charge(42.50).amount == 42.50

    def test_rejects_a_non_positive_charge(self, gateway):
        assert gateway.charge(0.0).status is PaymentStatus.ERROR

    def test_reports_a_non_empty_provider_name(self, gateway):
        assert gateway.get_provider_name()

    def test_round_trips_a_charge_and_refund(self, gateway):
        charge = gateway.charge(42.50)
        assert gateway.refund(charge.transaction_id).status is PaymentStatus.APPROVED


class TestInHouseLedgerGateway:
    """A first-party implementation proves the interface is a real boundary."""

    def test_is_a_payment_gateway(self):
        assert isinstance(InHouseLedgerGateway(), PaymentGateway)

    def test_approves_charge(self):
        assert InHouseLedgerGateway().charge(99.99).transaction_id == "LEDGER-00001"

    def test_normalizes_currency_to_upper_case(self):
        assert InHouseLedgerGateway().charge(1.00, "usd").currency == "USD"

    def test_refund_prefixes_the_ledger_id(self):
        ledger = InHouseLedgerGateway()
        assert ledger.refund("LEDGER-00001").transaction_id == "REV-LEDGER-00001"

    def test_refund_rejects_unknown_transaction(self):
        result = InHouseLedgerGateway().refund("PPTXN-0001")
        assert result.status is PaymentStatus.ERROR
        assert "Unknown transaction" in result.reason

    def test_requires_no_sdk(self):
        assert not hasattr(InHouseLedgerGateway(), "charge_cents")


class TestSmsSenderAdapter:
    """Translation: dict with a status string -> NotificationResult."""

    def test_is_a_notification_sender(self, sms_sender):
        assert isinstance(sms_sender, NotificationSender)

    def test_delivers_to_a_valid_number(self, sms_sender):
        result = sms_sender.send("+919876543210", "Your order shipped!")
        assert result.delivered
        assert result.message_id == "SM00000001"
        assert result.reason is None

    def test_result_channel_is_sms(self, sms_sender):
        assert sms_sender.send("+919876543210", "hi").channel is NotificationChannel.SMS

    def test_malformed_number_becomes_undelivered_result(self, sms_sender):
        result = sms_sender.send("98765", "oops")
        assert not result.delivered
        assert "Not an E.164 number" in result.reason

    def test_empty_body_becomes_undelivered_result(self, sms_sender):
        assert not sms_sender.send("+919876543210", "").delivered

    def test_over_long_message_becomes_undelivered_result(self, sms_sender):
        result = sms_sender.send("+919876543210", "x" * 500)
        assert not result.delivered
        assert result.reason == "MESSAGE_TOO_LONG"

    def test_sender_id_is_passed_to_the_sdk(self):
        sdk = LegacySmsSdk("sid", "token")
        SmsSenderAdapter(sdk, sender_id="SHOP9").send("+919876543210", "hi")
        assert sdk.calls[-1] == "send_text:+919876543210"

    def test_channel_name_is_reported(self, sms_sender):
        assert sms_sender.get_channel_name() is NotificationChannel.SMS

    def test_repr_mentions_channel(self, sms_sender):
        assert "sms" in repr(sms_sender)


class TestSmtpEmailSenderAdapter:
    """Translation: integer errno -> NotificationResult.delivered."""

    def test_is_a_notification_sender(self, email_sender):
        assert isinstance(email_sender, NotificationSender)

    def test_delivers_when_sender_is_configured(self, email_sender):
        result = email_sender.send("user@example.com", "Your order shipped!")
        assert result.delivered
        assert result.reason is None

    def test_result_channel_is_email(self, email_sender):
        assert email_sender.send("a@b.com", "hi").channel is NotificationChannel.EMAIL

    def test_missing_sender_surfaces_as_errno_reason(self):
        sender = SmtpEmailSenderAdapter(SmtpRelay("relay.local"))
        result = sender.send("user@example.com", "hi")
        assert not result.delivered
        assert result.reason == "smtp_errno_250"

    def test_bad_recipient_surfaces_as_errno_reason(self, email_sender):
        result = email_sender.send("not-an-email", "hi")
        assert not result.delivered
        assert result.reason == "smtp_errno_513"

    def test_error_code_never_raises(self, email_sender):
        email_sender.send("nonsense", "hi")  # must not raise

    def test_default_subject_satisfies_the_relay(self, email_sender):
        assert email_sender.send("user@example.com", "body").delivered

    def test_message_id_increments(self, email_sender):
        email_sender.send("a@b.com", "one")
        assert email_sender.send("a@b.com", "two").message_id == "smtp-00002"

    def test_channel_name_is_reported(self, email_sender):
        assert email_sender.get_channel_name() is NotificationChannel.EMAIL

    def test_sender_is_configured_on_the_relay(self):
        relay = SmtpRelay("relay.local")
        SmtpEmailSenderAdapter(relay, "no-reply@shop.io")
        assert relay.deliver(["a@b.com"], "Your order", "x") == 0


class TestClassAdapter:
    """The inheritance form: same contract, but the adaptee stays reachable."""

    def test_satisfies_the_same_interface(self):
        adapter = PayPalClassAdapter("client-id", "secret")
        assert isinstance(adapter, PaymentGateway)

    def test_also_inherits_the_adaptee(self):
        assert isinstance(PayPalClassAdapter("client-id", "secret"), LegacyPayPalSdk)

    def test_authenticates_in_the_constructor(self):
        adapter = PayPalClassAdapter("client-id", "secret")
        assert adapter.is_authenticated()
        assert adapter.calls[0] == "authenticate"

    def test_produces_the_same_result_as_the_object_adapter(self):
        class_adapter = PayPalClassAdapter("client-id", "secret")
        object_adapter = PayPalAdapter(LegacyPayPalSdk("client-id", "secret"))
        assert class_adapter.charge(42.50) == object_adapter.charge(42.50)

    def test_converts_units_and_states(self):
        result = PayPalClassAdapter("client-id", "secret").charge(42.50)
        assert result.status is PaymentStatus.APPROVED
        assert result.transaction_id == "PPTXN-0001"

    def test_declines_are_translated(self):
        assert PayPalClassAdapter("client-id", "secret").charge(5000.00).status is (
            PaymentStatus.DECLINED
        )

    def test_rejects_non_positive_charge(self):
        assert PayPalClassAdapter("client-id", "secret").charge(0.0).status is (
            PaymentStatus.ERROR
        )

    def test_refunds_a_charge(self):
        adapter = PayPalClassAdapter("client-id", "secret")
        charge = adapter.charge(10.00)
        assert adapter.refund(charge.transaction_id).status is PaymentStatus.APPROVED

    def test_reports_provider_name(self):
        assert PayPalClassAdapter("client-id", "secret").get_provider_name() == (
            "paypal-class"
        )

    def test_inherits_raw_sdk_methods(self):
        adapter = PayPalClassAdapter("client-id", "secret")
        assert hasattr(adapter, "charge_cents")

    def test_raw_sdk_method_bypasses_the_target_interface(self):
        adapter = PayPalClassAdapter("client-id", "secret")
        raw = adapter.charge_cents(1250, "USD")
        assert raw["state"] == "COMPLETED"

    def test_mro_puts_the_adaptee_first(self):
        mro = [cls.__name__ for cls in PayPalClassAdapter.__mro__]
        assert mro.index("LegacyPayPalSdk") < mro.index("PaymentGateway")


class TestObjectAdapterIsolation:
    """The benefit of composition: the adaptee is unreachable."""

    def test_paypal_adapter_exposes_only_target_methods(self, paypal):
        public = sorted(m for m in dir(paypal) if not m.startswith("_"))
        assert public == ["charge", "get_provider_name", "refund"]

    def test_acquirer_adapter_exposes_only_target_methods(self, acquirer):
        public = sorted(m for m in dir(acquirer) if not m.startswith("_"))
        assert public == ["charge", "get_provider_name", "refund"]

    def test_paypal_sdk_method_is_not_reachable(self, paypal):
        assert not hasattr(paypal, "charge_cents")

    def test_acquirer_sdk_method_is_not_reachable(self, acquirer):
        assert not hasattr(acquirer, "create_payment")

    def test_vendor_exception_type_is_not_reachable(self, paypal):
        assert not hasattr(paypal, "LegacySdkError")


class TestLeakyClient:
    """The 'before' picture: the same flow with every quirk leaking."""

    def test_authenticates_in_its_constructor(self, paypal_sdk):
        sms = LegacySmsSdk("sid", "token")
        LegacyCheckoutService(paypal_sdk, sms)
        assert paypal_sdk.calls == ["authenticate"]

    def test_approved_checkout_sends_the_sms(self, paypal_sdk):
        sms = LegacySmsSdk("sid", "token")
        service = LegacyCheckoutService(paypal_sdk, sms)
        assert service.checkout("+919876543210", 25.00, "order-1") == (
            "approved: PPTXN-0001"
        )
        assert sms.get_message_count() == 1

    def test_vendor_decline_surfaces_verbatim(self, paypal_sdk):
        service = LegacyCheckoutService(paypal_sdk, LegacySmsSdk("sid", "token"))
        assert service.checkout("+919876543210", 5000.00, "o") == (
            "declined: RISK_LIMIT_EXCEEDED"
        )

    def test_sms_failure_is_handled_separately(self, paypal_sdk):
        service = LegacyCheckoutService(paypal_sdk, LegacySmsSdk("sid", "token"))
        outcome = service.checkout("123", 25.00, "o")
        assert outcome.startswith("charged but no SMS")

    def test_client_talks_the_vendor_unit_scale(self, paypal_sdk):
        service = LegacyCheckoutService(paypal_sdk, LegacySmsSdk("sid", "token"))
        service.checkout("+919876543210", 25.00, "order-1")
        assert paypal_sdk.calls[-1] == "charge_cents:2500:USD"

    def test_client_reports_vendor_errors(self, paypal_sdk):
        service = LegacyCheckoutService(paypal_sdk, LegacySmsSdk("sid", "token"))
        assert service.checkout("+919876543210", 0.0, "o").startswith("error:")

    def test_a_second_provider_needs_a_branch(self, paypal_sdk):
        service = LegacyCheckoutService(paypal_sdk, LegacySmsSdk("sid", "token"))
        assert "backup" in service.checkout_with_backup_provider("+919876543210", 0.0)


class TestGatewayRegistry:
    """Name -> adapter lookup, so wiring is not an if/elif chain."""

    def test_lookup_is_case_insensitive(self):
        registry = GatewayRegistry()
        registry.build_default()
        assert registry.get_gateway("PAYPAL") is registry.get_gateway("paypal")

    def test_build_default_registers_three_gateways(self):
        registry = GatewayRegistry()
        registry.build_default()
        assert registry.supported_gateways() == ["acquirer", "inhouse", "paypal"]

    def test_build_default_registers_two_senders(self):
        registry = GatewayRegistry()
        registry.build_default()
        assert registry.supported_senders() == ["email", "sms"]

    def test_registered_gateways_are_payment_gateways(self):
        registry = GatewayRegistry()
        registry.build_default()
        for name in registry.supported_gateways():
            assert isinstance(registry.get_gateway(name), PaymentGateway)

    def test_registered_senders_are_notification_senders(self):
        registry = GatewayRegistry()
        registry.build_default()
        for name in registry.supported_senders():
            assert isinstance(registry.get_sender(name), NotificationSender)

    def test_unknown_gateway_raises_key_error(self):
        registry = GatewayRegistry()
        with pytest.raises(KeyError, match="bitcoin"):
            registry.get_gateway("bitcoin")

    def test_unknown_sender_raises_key_error(self):
        registry = GatewayRegistry()
        with pytest.raises(KeyError, match="carrier-pigeon"):
            registry.get_sender("carrier-pigeon")

    def test_new_provider_needs_no_other_change(self):
        registry = GatewayRegistry()
        registry.build_default()
        registry.register_gateway("crypto", InHouseLedgerGateway("crypto-rail"))
        assert isinstance(registry.get_gateway("crypto"), PaymentGateway)

    def test_re_registration_replaces_the_adapter(self):
        registry = GatewayRegistry()
        registry.build_default()
        registry.register_gateway("paypal", InHouseLedgerGateway("replacement"))
        assert registry.get_gateway("paypal").get_provider_name() == "replacement"

    def test_empty_registry_lists_nothing(self):
        registry = GatewayRegistry()
        assert registry.supported_gateways() == []


class TestCheckoutService:
    """Clean business logic: one implementation, every provider."""

    @pytest.fixture
    def registry(self):
        registry = GatewayRegistry()
        registry.build_default()
        return registry

    def test_successful_checkout_notifies_the_customer(self, registry):
        service = CheckoutService(registry.get_gateway("paypal"), registry.get_sender("sms"))
        outcome = service.checkout("+919876543210", 42.50, "USD", "order-1")
        assert outcome == {
            "ok": True,
            "status": "approved",
            "transaction_id": "PPTXN-0001",
            "reason": None,
            "notified": True,
        }

    def test_declined_checkout_skips_the_notification(self, registry):
        service = CheckoutService(registry.get_gateway("paypal"), registry.get_sender("sms"))
        outcome = service.checkout("+919876543210", 5000.00, "USD", "order-2")
        assert outcome["ok"] is False
        assert outcome["status"] == "declined"
        assert outcome["notified"] is False

    def test_error_checkout_skips_the_notification(self, registry):
        service = CheckoutService(registry.get_gateway("paypal"), registry.get_sender("sms"))
        outcome = service.checkout("+919876543210", 10.00, "JPY", "order-3")
        assert outcome["ok"] is False
        assert outcome["status"] == "error"
        assert outcome["notified"] is False

    def test_refund_reports_success(self, registry):
        service = CheckoutService(registry.get_gateway("paypal"), registry.get_sender("sms"))
        charge = service.checkout("+919876543210", 42.50, "USD", "order-4")
        assert service.refund(charge["transaction_id"])["ok"] is True

    def test_refund_reports_failure_for_unknown_id(self, registry):
        service = CheckoutService(registry.get_gateway("paypal"), registry.get_sender("sms"))
        assert service.refund("nope")["ok"] is False

    def test_works_against_every_registered_provider(self, registry):
        for name in registry.supported_gateways():
            service = CheckoutService(
                registry.get_gateway(name), registry.get_sender("sms")
            )
            outcome = service.checkout("+919876543210", 42.50, "USD", f"order-{name}")
            assert outcome["ok"] is True, name

    def test_email_sender_is_interchangeable_with_sms(self, registry):
        service = CheckoutService(
            registry.get_gateway("inhouse"), registry.get_sender("email")
        )
        assert service.checkout("a@b.com", 5.00, "USD", "order-5")["notified"] is True

    def test_service_source_names_no_vendor_detail(self):
        source = inspect.getsource(CheckoutService).lower()
        for token in VENDOR_TOKENS:
            assert token.lower() not in source, token

    def test_target_interfaces_name_no_vendor_detail(self):
        source = inspect.getsource(PaymentGateway) + inspect.getsource(NotificationSender)
        lowered = source.lower()
        for token in ("paypal", "acquirer", "smtp", "cents", "minor_units", "errno"):
            assert token not in lowered, token
