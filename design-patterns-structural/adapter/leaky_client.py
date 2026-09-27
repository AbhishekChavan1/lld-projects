"""
Adapter Pattern - The "before" picture: a leaky client

``LegacyCheckoutService`` is what you get when nobody writes an adapter.
It programs against ``LegacyPayPalSdk`` directly, which means:

- it hardcodes the vendor's minor-unit scale
- it performs the vendor's auth handshake itself
- it parses the vendor's string state codes
- it catches the vendor's exception type
- it cannot take a second provider without a branch

Every one of those lines is a change that has to be made again for the
next vendor. Compare with ``checkout_service.CheckoutService``, which is
the same business logic with none of it.
"""
from __future__ import annotations

from .legacy_paypal_sdk import LegacyPayPalSdk, LegacySdkError
from .notification_sdks import LegacySmsSdk, SmsDeliveryError

_PAYPAL_STATE_MAP = {
    "COMPLETED": "approved",
    "DECLINED": "declined",
}


class LegacyCheckoutService:
    """Business logic fused to one vendor. Every SDK quirk leaks in here."""

    def __init__(self, sdk: LegacyPayPalSdk, sms: LegacySmsSdk) -> None:
        self._sdk = sdk
        self._sms = sms
        if not self._sdk.is_authenticated():
            self._sdk.authenticate()

    def checkout(self, user_phone: str, amount: float, reference: str) -> str:
        try:
            cents = int(round(amount * self._sdk.MINOR_UNITS_PER_MAJOR))
            raw = self._sdk.charge_cents(cents, "USD", note=reference)
        except LegacySdkError as exc:
            return f"error: {exc}"

        status = _PAYPAL_STATE_MAP[raw["state"]]
        if status == "declined":
            return f"declined: {raw['err']}"

        try:
            self._sms.send_text(user_phone, f"Payment {raw['id']} approved")
        except SmsDeliveryError as exc:
            return f"charged but no SMS: {exc}"

        return f"approved: {raw['id']}"

    def checkout_with_backup_provider(self, user_phone: str, amount: float) -> str:
        """The cost of no adapter: a second provider needs a branch here."""
        primary = self.checkout(user_phone, amount, "order-1")
        if primary.startswith("error"):
            return "would retry on a backup provider (not implemented)"
        return primary
