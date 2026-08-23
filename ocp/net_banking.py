from payment_router import PaymentHandler


class NetBankingPaymentHandler(PaymentHandler):
    def process(self, amount: float) -> None:
        status = "Redirect to bank portal" if amount > 10000 else "Direct debit"
        print(f"[NetBanking] Processing {amount} via net banking. {status}")
