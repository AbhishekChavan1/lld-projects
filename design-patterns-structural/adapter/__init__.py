"""
Adapter Pattern - Third-party SDKs and the adapters around them

- ``ports``               target interfaces the application owns
- ``status_translation``  vendor state codes -> ``PaymentStatus``
- ``legacy_paypal_sdk``   adaptee: cents, dicts, mandatory auth, error codes
- ``acquirer_sdk``        adaptee: minor units, exceptions, partial refunds
- ``notification_sdks``   adaptors: SMS dict status vs. SMTP integer errno
- ``payment_adapters``    object adapters + a first-party implementation
- ``class_adapter``       inheritance-based adapter, for contrast
- ``leaky_client``        the "before" picture: no adapter, everything leaks
- ``registry``            name -> adapter lookup and the clean checkout flow
"""
from .acquirer_sdk import AcquirerError, ModernAcquirerSdk
from .class_adapter import PayPalClassAdapter
from .leaky_client import LegacyCheckoutService
from .legacy_paypal_sdk import LegacyPayPalSdk, LegacySdkError
from .notification_sdks import LegacySmsSdk, SmsDeliveryError, SmtpRelay
from .payment_adapters import (
    AcquirerAdapter,
    InHouseLedgerGateway,
    PayPalAdapter,
    SmtpEmailSenderAdapter,
    SmsSenderAdapter,
)
from .ports import (
    NotificationChannel,
    NotificationResult,
    NotificationSender,
    PaymentGateway,
    PaymentResult,
    PaymentStatus,
)
from .registry import CheckoutService, GatewayRegistry

__all__ = [
    "AcquirerAdapter",
    "AcquirerError",
    "CheckoutService",
    "GatewayRegistry",
    "InHouseLedgerGateway",
    "LegacyCheckoutService",
    "LegacyPayPalSdk",
    "LegacySmsSdk",
    "LegacySdkError",
    "ModernAcquirerSdk",
    "NotificationChannel",
    "NotificationResult",
    "NotificationSender",
    "PayPalAdapter",
    "PayPalClassAdapter",
    "PaymentGateway",
    "PaymentResult",
    "PaymentStatus",
    "SmsDeliveryError",
    "SmsSenderAdapter",
    "SmtpEmailSenderAdapter",
    "SmtpRelay",
]
