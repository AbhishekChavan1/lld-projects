"""
Adapter Pattern - Target Interfaces (the "ports" the application owns)

These are the interfaces the checkout service programs against. They are
written in *our* vocabulary: major currency units, dataclass results, a
small enum. No third-party SDK type appears anywhere in this file.

That is the whole point of the pattern: the target is defined by the
client, not by the vendor.

Where this fits in LLD:
- Payment abstraction over Stripe/PayPal/Razorpay/Adyen
- Notification abstraction over SMS/email/push SDKs
- Any time a vendor's SDK has an awkward shape and you refuse to let it
  leak into your domain

From The Design Round:
"Adapter converts the interface of a class into another interface a
client expects."
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class PaymentStatus(Enum):
    """Canonical payment outcome, independent of any vendor's vocabulary."""

    APPROVED = "approved"
    DECLINED = "declined"
    ERROR = "error"


class NotificationChannel(Enum):
    """Canonical channels, independent of any vendor's vocabulary."""

    SMS = "sms"
    EMAIL = "email"


@dataclass(frozen=True)
class PaymentResult:
    """Uniform payment outcome returned by every adapter."""

    transaction_id: str
    status: PaymentStatus
    amount: float
    currency: str
    vendor_reference: str | None = None
    reason: str | None = None

    @property
    def is_approved(self) -> bool:
        return self.status is PaymentStatus.APPROVED

    def __repr__(self) -> str:
        amount = f"{self.amount:.2f}" + (f" {self.currency}" if self.currency else "")
        return (
            f"PaymentResult(id={self.transaction_id!r}, "
            f"status={self.status.value}, amount={amount})"
        )


@dataclass(frozen=True)
class NotificationResult:
    """Uniform notification outcome returned by every adapter."""

    channel: NotificationChannel
    message_id: str
    delivered: bool
    reason: str | None = None

    def __repr__(self) -> str:
        return (
            f"NotificationResult(channel={self.channel.value}, "
            f"id={self.message_id!r}, delivered={self.delivered})"
        )


class PaymentGateway(ABC):
    """Target interface for charging and refunding.

    Implementations are either first-party (the in-house ledger) or
    adapters that wrap a third-party SDK.
    """

    @abstractmethod
    def charge(
        self, amount: float, currency: str = "USD", reference: str = ""
    ) -> PaymentResult:
        """Charge ``amount`` in MAJOR units (e.g. 12.50, not 1250)."""
        ...

    @abstractmethod
    def refund(self, transaction_id: str) -> PaymentResult:
        ...

    @abstractmethod
    def get_provider_name(self) -> str:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.get_provider_name()!r})"


class NotificationSender(ABC):
    """Target interface for outbound messages."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> NotificationResult:
        ...

    @abstractmethod
    def get_channel_name(self) -> NotificationChannel:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(channel={self.get_channel_name().value})"
