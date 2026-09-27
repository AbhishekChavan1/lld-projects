"""
Adapter Pattern - Class Adapter (inheritance), for contrast

A class adapter inherits from *both* the target and the adaptee, so it can
forward by calling ``super()`` instead of holding a reference.

It works, and ``PayPalClassAdapter`` satisfies ``PaymentGateway`` exactly
like the object adapter does. The difference is what it also inherits:
every public method of the adaptee stays reachable, so a client holding a
``PayPalClassAdapter`` can call ``charge_cents(1250, "USD")`` directly and
bypass the target interface entirely.

The compiler cannot stop that. With an object adapter, ``PayPalAdapter``
exposes only ``charge``/``refund``/``get_provider_name`` and the SDK is
unreachable through it.

Rule of thumb: prefer the object adapter. Reach for a class adapter only
when you cannot get hold of an adaptee *instance* to wrap.
"""
from __future__ import annotations

from .legacy_paypal_sdk import LegacyPayPalSdk, LegacySdkError
from .ports import PaymentGateway, PaymentResult, PaymentStatus
from .status_translation import PAYPAL_STATE_MAP


class PayPalClassAdapter(LegacyPayPalSdk, PaymentGateway):
    """Class adapter: inherits the SDK and implements the target.

    Note the MRO: ``LegacyPayPalSdk`` first, so the SDK's own methods are
    available and unhidden.
    """

    def __init__(self, client_id: str, client_secret: str) -> None:
        super().__init__(client_id, client_secret)
        self.authenticate()

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
        try:
            raw = self.charge_cents(
                int(round(amount * self.MINOR_UNITS_PER_MAJOR)),
                currency,
                note=reference,
            )
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
            raw = self.revert(transaction_id)
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
        return "paypal-class"
