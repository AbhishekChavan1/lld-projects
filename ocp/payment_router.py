from abc import ABC, abstractmethod


class PaymentHandler(ABC):
    @abstractmethod
    def process(self, amount: float) -> None:
        pass


class CardPaymentHandler(PaymentHandler):
    def process(self, amount: float) -> None:
        auth = "3DS required" if amount > 100 else "Normal"
        print(f"[Card] Processing {amount} via card gateway. Auth: {auth}")


class UPIPaymentHandler(PaymentHandler):
    def process(self, amount: float) -> None:
        mode = "OTP validation" if amount > 5000 else "Quick pay"
        print(f"[UPI] Processing {amount} via UPI. {mode}")


class WalletPaymentHandler(PaymentHandler):
    def process(self, amount: float) -> None:
        status = "OK" if amount >= 500 else "Low balance fallback"
        print(f"[Wallet] Processing {amount} via wallet. Balance check: {status}")


class PaymentRouter:
    def __init__(self):
        self._handlers: dict[str, PaymentHandler] = {}

    def register(self, payment_type: str, handler: PaymentHandler) -> None:
        self._handlers[payment_type.upper()] = handler

    def get_handler(self, payment_type: str) -> PaymentHandler:
        handler = self._handlers.get(payment_type.upper())
        if handler is None:
            raise ValueError(f"Unknown payment type: {payment_type}")
        return handler


def main():
    router = PaymentRouter()
    router.register("CARD", CardPaymentHandler())
    router.register("UPI", UPIPaymentHandler())
    router.register("WALLET", WalletPaymentHandler())

    for payment_type in ("CARD", "UPI", "WALLET"):
        print(f"Payment via {payment_type}:")
        router.get_handler(payment_type).process(250.0)

    try:
        router.get_handler("NETBANKING")
    except ValueError as e:
        print(f"[Main] Error: {e}")

    from net_banking import NetBankingPaymentHandler

    router.register("NETBANKING", NetBankingPaymentHandler())
    print("Payment via NETBANKING (added with zero existing-code changes):")
    router.get_handler("NETBANKING").process(250.0)


if __name__ == "__main__":
    main()
