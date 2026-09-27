"""
Bridge Pattern - IMPLEMENTOR side of "message x channel"

``Channel`` is the implementor. It answers one question only: *how do I
put this text in front of this recipient?*

Note what is absent. No import of ``Message``, no ``message_type``
parameter, no ``if channel == ...`` switch. Every method takes plain
strings and numbers. That one-way dependency is what lets a fourth
channel appear without touching a single message class - and what stops
this from collapsing into Strategy or a chain of ``if`` branches.

The three channels also disagree productively about the same three
strings, which is the whole point of routing through an implementor:

- SMS folds the subject into the body and refuses long messages
- Email keeps the subject and validates the address
- Push drops the subject entirely and enforces a title-length limit
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class ChannelKind(Enum):
    """Which channel a receipt came from. Part of the implementor's own
    vocabulary - the messages above never branch on it."""

    SMS = "sms"
    EMAIL = "email"
    PUSH = "push"


@dataclass(frozen=True)
class DeliveryReceipt:
    """What every channel returns, so callers can treat them alike."""

    channel: ChannelKind
    recipient: str
    message_id: str
    subject_used: bool
    body_length: int
    delivered: bool
    detail: str

    def __repr__(self) -> str:
        flag = "sent" if self.delivered else "failed"
        return f"DeliveryReceipt({self.channel.value}, {self.recipient}, {flag})"


class Channel(ABC):
    """Implementor: knows how to deliver, not what it is delivering."""

    #: Longest body this channel accepts before it truncates or refuses.
    max_body: int = 160

    @abstractmethod
    def kind(self) -> ChannelKind:
        ...

    @abstractmethod
    def deliver(self, recipient: str, subject: str, body: str) -> DeliveryReceipt:
        """Deliver one message. The only vocabulary shared with the caller
        is ``recipient``, ``subject`` and ``body`` - all plain values."""

    def _next_id(self, prefix: str, sequence: int) -> str:
        return f"{prefix}-{sequence:05d}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(kind={self.kind().value})"


class SmsChannel(Channel):
    """No subject line exists, so it is prepended to the body."""

    max_body = 480  # three 160-character segments

    def __init__(self, sender_id: str = "SHOPT") -> None:
        self._sender_id = sender_id
        self._sequence = 0

    def kind(self) -> ChannelKind:
        return ChannelKind.SMS

    def deliver(self, recipient: str, subject: str, body: str) -> DeliveryReceipt:
        self._sequence += 1
        message_id = self._next_id("sms", self._sequence)
        combined = f"{subject}: {body}" if subject else body

        if not recipient.startswith("+") or len(recipient) < 8:
            return DeliveryReceipt(
                channel=ChannelKind.SMS,
                recipient=recipient,
                message_id=message_id,
                subject_used=False,
                body_length=len(combined),
                delivered=False,
                detail="not an E.164 number",
            )
        if len(combined) > self.max_body:
            return DeliveryReceipt(
                channel=ChannelKind.SMS,
                recipient=recipient,
                message_id=message_id,
                subject_used=False,
                body_length=len(combined),
                delivered=False,
                detail=f"body over {self.max_body} characters",
            )
        return DeliveryReceipt(
            channel=ChannelKind.SMS,
            recipient=recipient,
            message_id=message_id,
            subject_used=False,
            body_length=len(combined),
            delivered=True,
            detail=f"from {self._sender_id}",
        )


class EmailChannel(Channel):
    """Keeps the subject, and is the only channel that validates an address."""

    max_body = 100_000

    def __init__(self, sender: str = "no-reply@shop.io") -> None:
        self._sender = sender
        self._sequence = 0

    def kind(self) -> ChannelKind:
        return ChannelKind.EMAIL

    def deliver(self, recipient: str, subject: str, body: str) -> DeliveryReceipt:
        self._sequence += 1
        message_id = self._next_id("mail", self._sequence)

        if "@" not in recipient or "." not in recipient.split("@")[-1]:
            return DeliveryReceipt(
                channel=ChannelKind.EMAIL,
                recipient=recipient,
                message_id=message_id,
                subject_used=bool(subject),
                body_length=len(body),
                delivered=False,
                detail="malformed address",
            )
        return DeliveryReceipt(
            channel=ChannelKind.EMAIL,
            recipient=recipient,
            message_id=message_id,
            subject_used=bool(subject),
            body_length=len(body),
            delivered=True,
            detail=f"from {self._sender}",
        )


class PushChannel(Channel):
    """Discards the subject (it becomes the notification title) and caps it."""

    max_body = 120

    def __init__(self, app_name: str = "shop") -> None:
        self._app_name = app_name
        self._sequence = 0

    def kind(self) -> ChannelKind:
        return ChannelKind.PUSH

    def deliver(self, recipient: str, subject: str, body: str) -> DeliveryReceipt:
        self._sequence += 1
        message_id = self._next_id("push", self._sequence)
        title = subject[:40]

        if not recipient.startswith("device-"):
            return DeliveryReceipt(
                channel=ChannelKind.PUSH,
                recipient=recipient,
                message_id=message_id,
                subject_used=False,
                body_length=len(body),
                delivered=False,
                detail="recipient is not a device token",
            )
        if len(title) > 40:
            return DeliveryReceipt(
                channel=ChannelKind.PUSH,
                recipient=recipient,
                message_id=message_id,
                subject_used=False,
                body_length=len(body),
                delivered=False,
                detail="title too long",
            )
        return DeliveryReceipt(
            channel=ChannelKind.PUSH,
            recipient=recipient,
            message_id=message_id,
            subject_used=bool(subject),
            body_length=len(body),
            delivered=True,
            detail=f"{self._app_name}: {title}",
        )
