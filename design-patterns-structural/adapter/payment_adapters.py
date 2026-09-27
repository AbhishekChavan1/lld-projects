"""
Adapter Pattern - Object Adapters (composition)

Each adapter *wraps* an adaptee in a field and translates between the two
interfaces. This is the form to reach for by default: the adaptee keeps
its own public surface, so nothing leaks and nothing is inherited.

Translation work per adapter:

``PayPalAdapter`` over ``LegacyPayPalSdk``
    major units -> integer cents
    authenticate lazily on first use
    ``dict`` + ``"COMPLETED"``/``"DECLINED"`` -> ``PaymentResult`` + ``PaymentStatus``
    ``LegacySdkError`` -> ``PaymentStatus.ERROR``
    vendor id preserved in ``vendor_reference`` so refunds work

``AcquirerAdapter`` over ``ModernAcquirerSdk``
    major units -> integer minor units
    ``AcquirerError`` -> ``PaymentStatus.ERROR`` (the *other* error convention)
    ``"succeeded"``/``"failed"`` -> ``PaymentStatus.APPROVED``/``DECLINED``
    free-form currency lowercased to the canonical upper-case form

``SmsSenderAdapter`` over ``LegacySmsSdk``
    str -> dict with ``"queued"``/``"failed"``

``SmtpEmailSenderAdapter`` over ``SmtpRelay``
    str + subject -> int errno (0 == success)
"""
from __future__ import annotations

from .acquirer_sdk import AcquirerError, ModernAcquirerSdk
from .legacy_paypal_sdk import LegacyPayPalSdk, LegacySdkError
from .notification_sdks import LegacySmsSdk, SmsDeliveryError, SmtpRelay
from .ports import (
    NotificationChannel,
    NotificationResult,
    NotificationSender,
    PaymentGateway,
    PaymentResult,
    PaymentStatus,
)
from .status_translation import ACQUIRER_STATE_MAP, PAYPAL_STATE_MAP


class PayPalAdapter(PaymentGateway):
    """Object adapter: wraps ``LegacyPayPalSdk`` behind ``PaymentGateway``."""

    def __init__(self, sdk: LegacyPayPalSdk, provider_name: str = "paypal") -> None:
        self._sdk = sdk
        self._provider_name = provider_name

    def charge(
        self, amount: float, currency: str = "USD", reference: str = ""
    ) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(
                transaction_id="",
                status=PaymentStatus.ERROR,
                amount=amount,
                currency=currency,
                reason="Charge amount must be positive",
            )

        cents = self._to_minor_units(amount)
        try:
            self._ensure_authenticated()
            raw = self._sdk.charge_cents(cents, currency, note=reference)
        except LegacySdkError as exc:
            return PaymentResult(
                transaction_id="",
                status=PaymentStatus.ERROR,
                amount=amount,
                currency=currency,
                reason=str(exc),
            )

        return PaymentResult(
            transaction_id=raw["id"],
            status=PAYPAL_STATE_MAP[raw["state"]],
            amount=amount,
            currency=currency,
            vendor_reference=raw["id"],
            reason=raw.get("err"),
        )

    def refund(self, transaction_id: str) -> PaymentResult:
        try:
            self._ensure_authenticated()
            raw = self._sdk.revert(transaction_id)
        except LegacySdkError as exc:
            return PaymentResult(
                transaction_id=transaction_id,
                status=PaymentStatus.ERROR,
                amount=0.0,
                currency="",
                reason=str(exc),
            )

        return PaymentResult(
            transaction_id=raw["id"],
            status=PAYPAL_STATE_MAP[raw["state"]],
            amount=0.0,
            currency="",
            vendor_reference=transaction_id,
        )

    def get_provider_name(self) -> str:
        return self._provider_name

    # --- translation helpers ----------------------------------------------

    def _ensure_authenticated(self) -> None:
        """Hide the SDK's mandatory auth handshake behind first use."""
        if not self._sdk.is_authenticated():
            self._sdk.authenticate()

    @staticmethod
    def _to_minor_units(amount: float) -> int:
        scale = LegacyPayPalSdk.MINOR_UNITS_PER_MAJOR
        return int(round(amount * scale))


class AcquirerAdapter(PaymentGateway):
    """Object adapter: wraps ``ModernAcquirerSdk`` behind ``PaymentGateway``."""

    def __init__(
        self, sdk: ModernAcquirerSdk, provider_name: str = "acquirer"
    ) -> None:
        self._sdk = sdk
        self._provider_name = provider_name

    def charge(
        self, amount: float, currency: str = "USD", reference: str = ""
    ) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(
                transaction_id="",
                status=PaymentStatus.ERROR,
                amount=amount,
                currency=currency,
                reason="Charge amount must be positive",
            )

        canonical_currency = currency.upper()
        minor_units = self._to_minor_units(amount)
        try:
            raw = self._sdk.create_payment(
                minor_units, canonical_currency.lower(), metadata={"ref": reference}
            )
        except AcquirerError as exc:
            return PaymentResult(
                transaction_id="",
                status=PaymentStatus.ERROR,
                amount=amount,
                currency=canonical_currency,
                reason=f"{exc.code}: {exc.reason}",
            )

        return PaymentResult(
            transaction_id=raw["payment_id"],
            status=ACQUIRER_STATE_MAP[raw["status"]],
            amount=amount,
            currency=canonical_currency,
            vendor_reference=raw["payment_id"],
            reason=raw.get("failure_reason"),
        )

    def refund(self, transaction_id: str) -> PaymentResult:
        try:
            raw = self._sdk.refund_payment(transaction_id)
        except AcquirerError as exc:
            return PaymentResult(
                transaction_id=transaction_id,
                status=PaymentStatus.ERROR,
                amount=0.0,
                currency="",
                reason=f"{exc.code}: {exc.reason}",
            )

        return PaymentResult(
            transaction_id=raw["refund_id"],
            status=ACQUIRER_STATE_MAP[raw["status"]],
            amount=0.0,
            currency="",
            vendor_reference=raw["payment_id"],
        )

    def get_provider_name(self) -> str:
        return self._provider_name

    @staticmethod
    def _to_minor_units(amount: float) -> int:
        scale = ModernAcquirerSdk.MINOR_UNITS_PER_MAJOR
        return int(round(amount * scale))


class InHouseLedgerGateway(PaymentGateway):
    """First-party implementation: already speaks our language, so it is not
    an adapter at all. It exists to prove the interface is a real boundary
    rather than a wrapper tax every provider must pay."""

    def __init__(self, provider_name: str = "inhouse") -> None:
        self._provider_name = provider_name
        self._sequence = 0

    def charge(
        self, amount: float, currency: str = "USD", reference: str = ""
    ) -> PaymentResult:
        if amount <= 0:
            return PaymentResult(
                transaction_id="",
                status=PaymentStatus.ERROR,
                amount=amount,
                currency=currency,
                reason="Charge amount must be positive",
            )
        self._sequence += 1
        txn_id = f"LEDGER-{self._sequence:05d}"
        return PaymentResult(
            transaction_id=txn_id,
            status=PaymentStatus.APPROVED,
            amount=amount,
            currency=currency.upper(),
            vendor_reference=txn_id,
        )

    def refund(self, transaction_id: str) -> PaymentResult:
        if not transaction_id.startswith("LEDGER-"):
            return PaymentResult(
                transaction_id=transaction_id,
                status=PaymentStatus.ERROR,
                amount=0.0,
                currency="",
                reason=f"Unknown transaction: {transaction_id}",
            )
        return PaymentResult(
            transaction_id=f"REV-{transaction_id}",
            status=PaymentStatus.APPROVED,
            amount=0.0,
            currency="",
            vendor_reference=transaction_id,
        )

    def get_provider_name(self) -> str:
        return self._provider_name


class SmsSenderAdapter(NotificationSender):
    """Object adapter: wraps ``LegacySmsSdk`` behind ``NotificationSender``."""

    def __init__(self, sdk: LegacySmsSdk, sender_id: str | None = None) -> None:
        self._sdk = sdk
        self._sender_id = sender_id

    def send(self, recipient: str, message: str) -> NotificationResult:
        try:
            raw = self._sdk.send_text(recipient, message, self._sender_id)
        except SmsDeliveryError as exc:
            return NotificationResult(
                channel=NotificationChannel.SMS,
                message_id="",
                delivered=False,
                reason=str(exc),
            )

        delivered = raw["status"] == "queued"
        return NotificationResult(
            channel=NotificationChannel.SMS,
            message_id=raw["sid"],
            delivered=delivered,
            reason=raw.get("error"),
        )

    def get_channel_name(self) -> NotificationChannel:
        return NotificationChannel.SMS


class SmtpEmailSenderAdapter(NotificationSender):
    """Object adapter: wraps ``SmtpRelay`` behind ``NotificationSender``.

    The relay has no concept of a single recipient or a mandatory subject,
    and it reports failure with a non-zero errno instead of an object.
    """

    DEFAULT_SUBJECT = "Notification"

    def __init__(self, relay: SmtpRelay, sender: str = "") -> None:
        self._relay = relay
        if sender:
            relay.set_sender(sender)

    def send(self, recipient: str, message: str) -> NotificationResult:
        code = self._relay.deliver(
            recipients=[recipient], subject=self.DEFAULT_SUBJECT, body=message
        )
        delivered = code == 0
        return NotificationResult(
            channel=NotificationChannel.EMAIL,
            message_id=f"smtp-{self._relay.get_delivery_count():05d}",
            delivered=delivered,
            reason=None if delivered else f"smtp_errno_{code}",
        )

    def get_channel_name(self) -> NotificationChannel:
        return NotificationChannel.EMAIL
