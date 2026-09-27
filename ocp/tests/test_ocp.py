import inspect

import pytest

from net_banking import NetBankingPaymentHandler
from payment_router import (
    CardPaymentHandler,
    PaymentHandler,
    PaymentRouter,
    UPIPaymentHandler,
    WalletPaymentHandler,
)


@pytest.fixture
def router():
    r = PaymentRouter()
    r.register("CARD", CardPaymentHandler())
    r.register("UPI", UPIPaymentHandler())
    r.register("WALLET", WalletPaymentHandler())
    return r


class TestPaymentHandlerContract:
    def test_base_is_abstract(self):
        with pytest.raises(TypeError):
            PaymentHandler()

    def test_every_handler_implements_process(self):
        for handler in (
            CardPaymentHandler(),
            UPIPaymentHandler(),
            WalletPaymentHandler(),
            NetBankingPaymentHandler(),
        ):
            assert isinstance(handler, PaymentHandler)
            assert callable(handler.process)

    def test_handlers_expose_only_process(self):
        public = [m for m in dir(CardPaymentHandler) if not m.startswith("_")]
        assert public == ["process"]


class TestRouterRegistration:
    def test_starts_empty(self):
        assert PaymentRouter()._handlers == {}

    def test_lookup_is_case_insensitive(self, router):
        assert isinstance(router.get_handler("card"), CardPaymentHandler)
        assert isinstance(router.get_handler("CARD"), CardPaymentHandler)
        assert isinstance(router.get_handler("CaRd"), CardPaymentHandler)

    def test_returns_the_registered_instance(self, router):
        handler = CardPaymentHandler()
        r = PaymentRouter()
        r.register("CARD", handler)
        assert r.get_handler("CARD") is handler

    def test_unknown_type_raises(self, router):
        with pytest.raises(ValueError, match="Unknown payment type: CRYPTO"):
            router.get_handler("CRYPTO")

    def test_unknown_type_error_names_the_type(self, router):
        with pytest.raises(ValueError, match="NETBANKING"):
            router.get_handler("NETBANKING")

    def test_reregistering_replaces_the_handler(self):
        r = PaymentRouter()
        r.register("CARD", CardPaymentHandler())
        r.register("card", WalletPaymentHandler())
        assert isinstance(r.get_handler("CARD"), WalletPaymentHandler)
        assert len(r._handlers) == 1


class TestHandlerBehaviour:
    def test_card_small_amount(self, capsys):
        CardPaymentHandler().process(50.0)
        assert "Auth: Normal" in capsys.readouterr().out

    def test_card_large_amount_requires_3ds(self, capsys):
        CardPaymentHandler().process(250.0)
        assert "3DS required" in capsys.readouterr().out

    def test_card_threshold_is_strictly_greater_than_100(self, capsys):
        CardPaymentHandler().process(100.0)
        assert "Auth: Normal" in capsys.readouterr().out

    def test_upi_small_amount(self, capsys):
        UPIPaymentHandler().process(250.0)
        assert "Quick pay" in capsys.readouterr().out

    def test_upi_large_amount(self, capsys):
        UPIPaymentHandler().process(5000.01)
        assert "OTP validation" in capsys.readouterr().out

    def test_wallet_low_balance(self, capsys):
        WalletPaymentHandler().process(499.0)
        assert "Low balance fallback" in capsys.readouterr().out

    def test_wallet_sufficient_balance(self, capsys):
        WalletPaymentHandler().process(500.0)
        assert "Balance check: OK" in capsys.readouterr().out

    def test_net_banking_direct_debit(self, capsys):
        NetBankingPaymentHandler().process(250.0)
        out = capsys.readouterr().out
        assert "Direct debit" in out
        assert "[NetBanking]" in out

    def test_net_banking_large_amount_redirects(self, capsys):
        NetBankingPaymentHandler().process(10000.01)
        assert "Redirect to bank portal" in capsys.readouterr().out

    def test_router_dispatches_to_each_handler(self, router, capsys):
        router.get_handler("CARD").process(250.0)
        router.get_handler("UPI").process(250.0)
        router.get_handler("WALLET").process(250.0)
        out = capsys.readouterr().out
        assert "[Card]" in out
        assert "[UPI]" in out
        assert "[Wallet]" in out


class TestOpenClosedPrinciple:
    def test_new_handler_needs_no_router_change(self, router, capsys):
        class CryptoPaymentHandler(PaymentHandler):
            def process(self, amount: float) -> None:
                print(f"[Crypto] Processing {amount} on-chain.")

        router.register("CRYPTO", CryptoPaymentHandler())
        router.get_handler("crypto").process(1000.0)
        assert "[Crypto] Processing 1000.0 on-chain." in capsys.readouterr().out

    def test_router_source_has_no_payment_type_branches(self):
        """The router must not name any concrete payment method."""
        source = inspect.getsource(PaymentRouter)
        for banned in ("CARD", "UPI", "WALLET", "NETBANKING", "isinstance"):
            assert banned not in source

    def test_router_only_dispatches(self):
        public = [m for m in dir(PaymentRouter) if not m.startswith("_")]
        assert public == ["get_handler", "register"]
