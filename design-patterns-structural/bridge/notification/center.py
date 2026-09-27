"""
Wiring for "message x channel"

A registry, nothing clever. It exists so the demo and the tests can say
"send every message over every channel" without a factory: the caller
constructs the message with the channel it wants, which keeps the pairing
explicit and keeps Bridge out of Factory Pattern business.
"""
from __future__ import annotations

from .abstraction import Message
from .implementor import Channel, DeliveryReceipt


class NotificationCenter:
    """Name -> channel. Configuration, not policy."""

    def __init__(self) -> None:
        self._channels: dict[str, Channel] = {}

    def register(self, name: str, channel: Channel) -> None:
        self._channels[name.lower()] = channel

    def channel(self, name: str) -> Channel:
        return self._channels[name.lower()]

    def names(self) -> list[str]:
        return sorted(self._channels)

    def send(self, message: Message, recipient: str) -> DeliveryReceipt:
        """Deliver through the channel the message was built with."""
        return message.send(recipient)
