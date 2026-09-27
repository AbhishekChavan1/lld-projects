"""
Adapter Pattern - Adaptee #2: a modern Acquirer-style SDK

A *different* vendor with a *different* set of awkwardness, so the two
adapters cannot be copy-pasted from each other:

- no authentication step, but an API key is validated eagerly
- failures are raised as exceptions, not returned as error codes
- the money argument is still integer minor units, but the currency is
  lowercased and free-form
- ``refund_payment`` accepts a partial amount
- the result key is ``payment_id`` and the status is lowercase

The adapter's job is to flatten two incompatible error conventions
(raise vs. return-a-code) into the single ``PaymentStatus`` enum.
"""
from __future__ import annotations

from typing import TypedDict


class AcquirerPayment(TypedDict):
    """Shape of the dict this vendor returns when creating a payment."""

    payment_id: str
    status: str
    failure_reason: str | None
    metadata: dict[str, str]


class AcquirerRefund(TypedDict):
    """Shape of the dict this vendor returns for a refund."""

    refund_id: str
    payment_id: str
    status: str
    amount_minor: int | None


class AcquirerError(Exception):
    """Transport/protocol failure. Carries a machine-readable reason."""

    def __init__(self, reason: str, code: str = "transport_error") -> None:
        super().__init__(reason)
        self.reason = reason
        self.code = code


class ModernAcquirerSdk:
    """Simulated third-party SDK. Treat its interface as fixed."""

    MINOR_UNITS_PER_MAJOR = 100

    def __init__(self, api_key: str, transport_ok: bool = True) -> None:
        if not api_key:
            raise AcquirerError("API key is required", code="auth_error")
        self._api_key = api_key
        self.transport_ok = transport_ok
        self._payment_sequence = 0
        self.calls: list[str] = []

    def create_payment(
        self, amount_minor: int, currency: str, metadata: dict[str, str] | None = None
    ) -> AcquirerPayment:
        """Create a payment. Raises AcquirerError instead of returning a code."""
        if not self.transport_ok:
            raise AcquirerError("Connection reset by peer", code="transport_error")
        if amount_minor <= 0:
            raise AcquirerError("Amount must be positive", code="invalid_amount")

        self._payment_sequence += 1
        payment_id = f"acq_{self._payment_sequence:05d}"
        self.calls.append(f"create_payment:{amount_minor}:{currency}")

        # This vendor hard-declines anything at or above 50_000 minor units.
        if amount_minor >= 50_000:
            return {
                "payment_id": payment_id,
                "status": "failed",
                "failure_reason": "amount_exceeds_merchant_tier",
                "metadata": metadata or {},
            }
        return {
            "payment_id": payment_id,
            "status": "succeeded",
            "failure_reason": None,
            "metadata": metadata or {},
        }

    def refund_payment(
        self, payment_id: str, amount_minor: int | None = None
    ) -> AcquirerRefund:
        if not self.transport_ok:
            raise AcquirerError("Connection reset by peer", code="transport_error")
        if not payment_id.startswith("acq_"):
            raise AcquirerError(f"Unknown payment id: {payment_id}", code="not_found")
        self.calls.append(f"refund_payment:{payment_id}")
        return {
            "refund_id": f"re_{payment_id}",
            "payment_id": payment_id,
            "status": "refunded",
            "amount_minor": amount_minor,
        }

    def get_payment_count(self) -> int:
        return self._payment_sequence
