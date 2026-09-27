"""
Adapter Pattern - Translation tables (vendor code -> canonical enum)

Kept separate because this mapping is *adapter* knowledge, not SDK
knowledge: the vendor knows nothing about ``PaymentStatus``, and
``ports`` knows nothing about ``"COMPLETED"``.

Both the object adapter and the class adapter translate the same PayPal
state codes, so there is exactly one place to edit when a vendor renames
one of them.
"""
from __future__ import annotations

from .ports import PaymentStatus

PAYPAL_STATE_MAP: dict[str, PaymentStatus] = {
    "COMPLETED": PaymentStatus.APPROVED,
    "DECLINED": PaymentStatus.DECLINED,
    "REFUNDED": PaymentStatus.APPROVED,
}

ACQUIRER_STATE_MAP: dict[str, PaymentStatus] = {
    "succeeded": PaymentStatus.APPROVED,
    "refunded": PaymentStatus.APPROVED,
    "failed": PaymentStatus.DECLINED,
}
