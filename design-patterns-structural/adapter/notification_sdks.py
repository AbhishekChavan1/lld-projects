"""
Adapter Pattern - Adaptees #3 and #4: notification SDKs

Two vendors whose interfaces have nothing in common beyond "send text":

``LegacySmsSdk``
    - requires an E.164 number, raises on a malformed one
    - optional ``sender_id`` (an alphanumeric sender, not a phone number)
    - returns a dict with ``sid`` / ``status`` (``queued`` | ``failed``)

``SmtpRelay``
    - no notion of SMS at all; it takes a *list* of recipients
    - a subject line is mandatory
    - signals success with a return code: ``0`` means OK, anything else
      is an errno
    - refuses to relay if no sender is configured

The two adapters therefore translate genuinely different things: a dict
with a status string, versus an integer errno.
"""
from __future__ import annotations


class SmsDeliveryError(Exception):
    """Raised when the SMS gateway itself is misused (bad number, etc.)."""


class LegacySmsSdk:
    """Simulated third-party SMS SDK."""

    MAX_SEGMENTS = 3

    def __init__(self, account_sid: str, auth_token: str) -> None:
        if not account_sid or not auth_token:
            raise SmsDeliveryError("Missing SMS credentials")
        self._account_sid = account_sid
        self._auth_token = auth_token
        self._sequence = 0
        self.calls: list[str] = []

    def send_text(
        self, to_number: str, body: str, sender_id: str | None = None
    ) -> dict:
        if not to_number.startswith("+") or len(to_number) < 8:
            raise SmsDeliveryError(f"Not an E.164 number: {to_number!r}")
        if not body:
            raise SmsDeliveryError("Message body cannot be empty")

        self._sequence += 1
        self.calls.append(f"send_text:{to_number}")

        # Anything over 160 chars is billed as extra segments; the demo
        # gateway rejects once the cap is exceeded.
        if len(body) > 160 * self.MAX_SEGMENTS:
            return {
                "sid": f"SM{self._sequence:08d}",
                "status": "failed",
                "error": "MESSAGE_TOO_LONG",
            }
        return {
            "sid": f"SM{self._sequence:08d}",
            "status": "queued",
            "error": None,
            "sender": sender_id or self._account_sid,
        }

    def get_message_count(self) -> int:
        return self._sequence


class SmtpRelay:
    """Simulated SMTP relay. Integer return codes, list recipients."""

    def __init__(self, relay_host: str, sender: str = "") -> None:
        self._relay_host = relay_host
        self._sender = sender
        self._sequence = 0
        self.calls: list[str] = []

    def set_sender(self, address: str) -> None:
        self._sender = address

    def deliver(self, recipients: list[str], subject: str, body: str) -> int:
        """Deliver a message. Returns 0 on success, else an errno code."""
        self._sequence += 1
        self.calls.append(f"deliver:{len(recipients)}")

        if not self._sender:
            return 250  # 5.x.x - sender not configured
        if not recipients or any("@" not in r for r in recipients):
            return 513  # bad or missing recipient address
        if len(subject.strip()) < 5:
            return 554  # transaction failed - subject line too short
        return 0

    def get_delivery_count(self) -> int:
        return self._sequence
