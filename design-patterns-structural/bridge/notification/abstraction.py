"""
Bridge Pattern - ABSTRACTION side of "message x channel"

``Message`` is the abstraction. It knows *what* is being said and delegates
*how* it is delivered to the ``Channel`` it was constructed with.

The relationship is composition: every message holds one channel for life.
There is no ``class SmsOtpMessage(OtpMessage)`` anywhere, and there never
should be - that inheritance would reappear once per channel per message.

``send()`` is a template method. The flow (ask the implementor to deliver)
is fixed here; the wording (subject, body) is what subclasses supply. New
message types therefore add one class and no edits anywhere else.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from .implementor import Channel, DeliveryReceipt


class Message(ABC):
    """Abstraction: content plus a reference to its implementor."""

    def __init__(self, channel: Channel) -> None:
        self._channel = channel

    @property
    def channel(self) -> Channel:
        return self._channel

    @abstractmethod
    def subject(self) -> str:
        ...

    @abstractmethod
    def body(self) -> str:
        ...

    def send(self, recipient: str) -> DeliveryReceipt:
        """Fixed flow, variable wording. The channel gets strings, never a
        ``Message``, which is what keeps the dependency one-directional."""
        return self._channel.deliver(recipient, self.subject(), self.body())

    def describe(self) -> str:
        return f"{self.__class__.__name__} -> {self._channel.kind().value}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._channel!r})"


class OtpMessage(Message):
    """A login code. Channels differ on where the code ends up: the body
    for SMS, the subject for push, both for email."""

    def __init__(self, channel: Channel, code: str, minutes: int = 10) -> None:
        super().__init__(channel)
        self._code = code
        self._minutes = minutes

    def subject(self) -> str:
        return f"{self._code} is your login code"

    def body(self) -> str:
        return f"Use this code within {self._minutes} minutes. Never share it."


class OrderShippedMessage(Message):
    """A fulfilment update with a long, channel-hostile body."""

    def __init__(
        self,
        channel: Channel,
        order_id: str,
        carrier: str,
        eta_days: int = 3,
    ) -> None:
        super().__init__(channel)
        self._order_id = order_id
        self._carrier = carrier
        self._eta_days = eta_days

    def subject(self) -> str:
        return f"Order {self._order_id} shipped"

    def body(self) -> str:
        return (
            f"{self._carrier} has your parcel. Expected in {self._eta_days} "
            f"business days. Track it in your account."
        )


class PaymentReceiptMessage(Message):
    """Financial detail, deliberately unsuitable for a 160-char channel -
    the SMS implementor decides what to do about that, not this class."""

    def __init__(self, channel: Channel, amount: str, last4: str) -> None:
        super().__init__(channel)
        self._amount = amount
        self._last4 = last4

    def subject(self) -> str:
        return "Payment received"

    def body(self) -> str:
        return f"We charged {self._amount} to the card ending {self._last4}."
