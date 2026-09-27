"""
Adapter Pattern - Adaptee #1: a legacy PayPal-style SDK

Third-party code we do not own and cannot change. Every design decision
here is deliberately awkward, because that is what real legacy SDKs look
like:

- amounts are integer MINOR units (cents), not floats
- the caller must authenticate before any other call, or it raises
- results are untyped dicts with string state codes
- failures come back as data (``err`` key), not as exceptions
- only a fixed set of currency codes is accepted
- transaction ids are prefixed and must be echoed back verbatim to refund

None of this may leak past the adapter. See ``payment_adapters.PayPalAdapter``.
"""
from __future__ import annotations

from typing import TypedDict


class PayPalCharge(TypedDict):
    """Shape of the dict this vendor returns for a charge."""

    id: str
    state: str
    err: str | None
    note: str


class PayPalRefund(TypedDict):
    """Shape of the dict this vendor returns for a refund."""

    id: str
    state: str
    err: str | None


class LegacySdkError(Exception):
    """Raised for misuse of the SDK (not for declined payments)."""


class LegacyPayPalSdk:
    """Simulated third-party SDK. Treat its interface as fixed."""

    MINOR_UNITS_PER_MAJOR = 100
    SUPPORTED_CURRENCIES = ("USD", "EUR")
    RISK_LIMIT_MINOR = 100_000  # declines anything above 1000.00

    def __init__(self, client_id: str, client_secret: str, debug: bool = False) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._debug = debug
        self._authenticated = False
        self._charge_sequence = 0
        self.calls: list[str] = []

    # --- session -----------------------------------------------------------

    def authenticate(self) -> bool:
        if not self._client_id or not self._client_secret:
            raise LegacySdkError("Missing client credentials")
        self._authenticated = True
        self.calls.append("authenticate")
        return True

    def set_debug(self, flag: bool) -> None:
        self._debug = flag

    def is_authenticated(self) -> bool:
        return self._authenticated

    # --- money -------------------------------------------------------------

    def charge_cents(
        self, cents: int, currency_code: str, note: str = ""
    ) -> PayPalCharge:
        """Charge an integer number of minor units.

        Returns a dict shaped like::

            {"id": "PPTXN-0001", "state": "COMPLETED", "err": None, "note": note}
            {"id": "PPTXN-0002", "state": "DECLINED", "err": "RISK_LIMIT_EXCEEDED"}
        """
        self._require_auth()
        if currency_code not in self.SUPPORTED_CURRENCIES:
            raise LegacySdkError(f"Unsupported currency: {currency_code}")
        if cents <= 0:
            raise LegacySdkError("Charge amount must be positive")

        self._charge_sequence += 1
        txn_id = f"PPTXN-{self._charge_sequence:04d}"
        self.calls.append(f"charge_cents:{cents}:{currency_code}")

        if cents > self.RISK_LIMIT_MINOR:
            return {
                "id": txn_id,
                "state": "DECLINED",
                "err": "RISK_LIMIT_EXCEEDED",
                "note": note,
            }
        return {"id": txn_id, "state": "COMPLETED", "err": None, "note": note}

    def revert(self, charge_id: str) -> PayPalRefund:
        """Refund a previous charge. Requires the exact vendor id."""
        self._require_auth()
        if not charge_id.startswith("PPTXN-"):
            raise LegacySdkError(f"Unknown charge id: {charge_id}")
        self.calls.append(f"revert:{charge_id}")
        return {
            "id": f"PPREF-{charge_id}",
            "state": "REFUNDED",
            "err": None,
        }

    def get_charge_count(self) -> int:
        return self._charge_sequence

    # --- internals ---------------------------------------------------------

    def _require_auth(self) -> None:
        if not self._authenticated:
            raise LegacySdkError("Not authenticated: call authenticate() first")
