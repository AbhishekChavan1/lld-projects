"""
Bridge Pattern - "message x channel"

``Message`` (abstraction) x ``Channel`` (implementor).
"""
from .abstraction import Message, OtpMessage, OrderShippedMessage, PaymentReceiptMessage
from .center import NotificationCenter
from .implementor import Channel, ChannelKind, DeliveryReceipt, EmailChannel, PushChannel, SmsChannel

__all__ = [
    "Channel",
    "ChannelKind",
    "DeliveryReceipt",
    "EmailChannel",
    "Message",
    "NotificationCenter",
    "OtpMessage",
    "OrderShippedMessage",
    "PaymentReceiptMessage",
    "PushChannel",
    "SmsChannel",
]
