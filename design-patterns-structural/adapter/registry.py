"""
Adapter Pattern - Registry and the vendor-agnostic checkout service

``GatewayRegistry`` maps a name to a ready-made adapter. It is a plain
dict lookup, so wiring a new provider is a ``register`` call and never an
``if``/``elif`` in business logic.

``CheckoutService`` is the payoff: it is the same business flow as
``leaky_client.LegacyCheckoutService``, but it mentions no vendor, no
minor-unit scale, no auth handshake, and no vendor exception type.
"""
from __future__ import annotations

from typing import TypedDict

from .acquirer_sdk import ModernAcquirerSdk
from .legacy_paypal_sdk import LegacyPayPalSdk
from .notification_sdks import LegacySmsSdk, SmtpRelay
from .payment_adapters import (
    AcquirerAdapter,
    InHouseLedgerGateway,
    PayPalAdapter,
    SmtpEmailSenderAdapter,
    SmsSenderAdapter,
)
from .ports import NotificationSender, PaymentGateway, PaymentStatus


class CheckoutOutcome(TypedDict):
    """Result of a checkout attempt. Typed, so callers get real field types."""

    ok: bool
    status: str
    transaction_id: str
    reason: str | None
    notified: bool


class RefundOutcome(TypedDict):
    """Result of a refund attempt."""

    ok: bool
    status: str
    transaction_id: str
    reason: str | None


class GatewayRegistry:
    """Name -> adapter lookup. No branching on provider identity."""

    def __init__(self) -> None:
        self._gateways: dict[str, PaymentGateway] = {}
        self._senders: dict[str, NotificationSender] = {}

    def register_gateway(self, name: str, gateway: PaymentGateway) -> None:
        self._gateways[name.lower()] = gateway

    def get_gateway(self, name: str) -> PaymentGateway:
        gateway = self._gateways.get(name.lower())
        if gateway is None:
            raise KeyError(f"No payment gateway registered as {name!r}")
        return gateway

    def register_sender(self, name: str, sender: NotificationSender) -> None:
        self._senders[name.lower()] = sender

    def get_sender(self, name: str) -> NotificationSender:
        sender = self._senders.get(name.lower())
        if sender is None:
            raise KeyError(f"No notification sender registered as {name!r}")
        return sender

    def supported_gateways(self) -> list[str]:
        return sorted(self._gateways)

    def supported_senders(self) -> list[str]:
        return sorted(self._senders)

    def build_default(self) -> None:
        """Wire the two third-party SDKs and the first-party ledger."""
        self.register_gateway(
            "paypal", PayPalAdapter(LegacyPayPalSdk("client-id", "secret"))
        )
        self.register_gateway(
            "acquirer", AcquirerAdapter(ModernAcquirerSdk("api-key"))
        )
        self.register_gateway("inhouse", InHouseLedgerGateway())
        self.register_sender("sms", SmsSenderAdapter(LegacySmsSdk("sid", "token")))
        self.register_sender(
            "email",
            SmtpEmailSenderAdapter(SmtpRelay("relay.local"), "no-reply@shop.io"),
        )


class CheckoutService:
    """Business logic that knows only the target interfaces.

    No vendor name, no money scale, no auth handshake and no vendor
    exception type appears in this class. Choosing a provider is the
    caller's decision, made through the constructor.
    """

    def __init__(
        self, gateway: PaymentGateway, notifier: NotificationSender
    ) -> None:
        self._gateway = gateway
        self._notifier = notifier

    def checkout(
        self, recipient: str, amount: float, currency: str, reference: str
    ) -> CheckoutOutcome:
        result = self._gateway.charge(amount, currency, reference)

        if not result.is_approved:
            return {
                "ok": False,
                "status": result.status.value,
                "transaction_id": result.transaction_id,
                "reason": result.reason,
                "notified": False,
            }

        notification = self._notifier.send(
            recipient, f"Payment {result.transaction_id} approved"
        )
        return {
            "ok": True,
            "status": result.status.value,
            "transaction_id": result.transaction_id,
            "reason": None,
            "notified": notification.delivered,
        }

    def refund(self, transaction_id: str) -> RefundOutcome:
        result = self._gateway.refund(transaction_id)
        return {
            "ok": result.status is PaymentStatus.APPROVED,
            "status": result.status.value,
            "transaction_id": result.transaction_id,
            "reason": result.reason,
        }
