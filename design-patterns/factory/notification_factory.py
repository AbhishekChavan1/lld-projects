"""
Factory Pattern - Notification Channel Factory (Factory Method)

Each notification channel (Email, SMS, Push) has different creation
logic and configuration. The Factory Method pattern lets each
concrete creator decide which product to instantiate.

Where this fits in LLD:
- Notification Service: NotificationChannelFactory.create(channel_type)
- Each channel has its own setup (SMTP server, SMS provider, push cert)
- Adding a new channel (WhatsApp) means adding a new creator subclass

From The Design Round:
"Factory centralizes creation, giving you one place to change
when types change."
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


class ChannelType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationChannel(ABC):
    """Abstract product - all channels implement send()."""

    @abstractmethod
    def send(self, recipient: str, message: str) -> str:
        ...

    @abstractmethod
    def get_channel_name(self) -> str:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class EmailChannel(NotificationChannel):
    def __init__(self, smtp_host: str = "smtp.example.com", port: int = 587) -> None:
        self.smtp_host = smtp_host
        self.port = port

    def send(self, recipient: str, message: str) -> str:
        return f"[EMAIL via {self.smtp_host}:{self.port}] To: {recipient} | {message}"

    def get_channel_name(self) -> str:
        return "email"


class SMSChannel(NotificationChannel):
    def __init__(self, provider: str = "Twilio") -> None:
        self.provider = provider

    def send(self, recipient: str, message: str) -> str:
        return f"[SMS via {self.provider}] To: {recipient} | {message}"

    def get_channel_name(self) -> str:
        return "sms"


class PushChannel(NotificationChannel):
    def __init__(self, service: str = "FCM") -> None:
        self.service = service

    def send(self, recipient: str, message: str) -> str:
        return f"[PUSH via {self.service}] To: {recipient} | {message}"

    def get_channel_name(self) -> str:
        return "push"


class NotificationChannelFactory:
    """
    Factory Method pattern with a registry.
    Each channel type maps to a creator function.
    """

    _creators: dict[ChannelType, type[NotificationChannel]] = {
        ChannelType.EMAIL: EmailChannel,
        ChannelType.SMS: SMSChannel,
        ChannelType.PUSH: PushChannel,
    }

    @classmethod
    def create(cls, channel_type: ChannelType, **kwargs) -> NotificationChannel:
        creator = cls._creators.get(channel_type)
        if creator is None:
            raise ValueError(f"Unknown channel type: {channel_type}")
        return creator(**kwargs)

    @classmethod
    def register(cls, channel_type: ChannelType, creator: type[NotificationChannel]) -> None:
        cls._creators[channel_type] = creator

    @classmethod
    def supported_channels(cls) -> list[ChannelType]:
        return list(cls._creators.keys())


# --- Factory Method variant: subclass-based creation ---

class NotificationCreator(ABC):
    """Abstract creator with a factory method."""

    @abstractmethod
    def create_channel(self) -> NotificationChannel:
        ...

    def send_notification(self, recipient: str, message: str) -> str:
        channel = self.create_channel()
        return channel.send(recipient, message)


class EmailCreator(NotificationCreator):
    def __init__(self, smtp_host: str = "smtp.example.com") -> None:
        self.smtp_host = smtp_host

    def create_channel(self) -> EmailChannel:
        return EmailChannel(smtp_host=self.smtp_host)


class SMSCreator(NotificationCreator):
    def __init__(self, provider: str = "Twilio") -> None:
        self.provider = provider

    def create_channel(self) -> SMSChannel:
        return SMSChannel(provider=self.provider)
