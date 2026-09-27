"""
Design Patterns - Structural: Adapter

Run: python main.py
"""
from adapter.acquirer_sdk import ModernAcquirerSdk
from adapter.class_adapter import PayPalClassAdapter
from adapter.leaky_client import LegacyCheckoutService
from adapter.legacy_paypal_sdk import LegacyPayPalSdk
from adapter.notification_sdks import LegacySmsSdk, SmtpRelay
from adapter.payment_adapters import (
    AcquirerAdapter,
    InHouseLedgerGateway,
    PayPalAdapter,
    SmtpEmailSenderAdapter,
    SmsSenderAdapter,
)
from adapter.registry import CheckoutService, GatewayRegistry


def separator(title: str) -> None:
    print(f"\n{'=' * 62}")
    print(f"  {title}")
    print(f"{'=' * 62}\n")


def demo_leaky_client() -> None:
    separator("ADAPTER: The problem (no adapter, vendor leaks everywhere)")
    print("LegacyCheckoutService programs against LegacyPayPalSdk directly:")
    print("  - it must multiply by the vendor's minor-unit scale")
    print("  - it must run the vendor's auth handshake")
    print("  - it must parse the vendor's string state codes")
    print("  - it must catch the vendor's exception type\n")

    sdk = LegacyPayPalSdk("client-id", "secret")
    sms = LegacySmsSdk("sid", "token")
    service = LegacyCheckoutService(sdk, sms)

    print(f"checkout(25.00)   -> {service.checkout('+919876543210', 25.00, 'order-1')}")
    print(f"checkout(5000.00) -> {service.checkout('+919876543210', 5000.00, 'order-2')}")
    print(f"  (declined by the vendor's risk rule, not by us)")
    print(f"\nSDK calls the service had to make: {sdk.calls}")
    print("Note: a second provider would need a branch inside this class.")


def demo_object_adapters() -> None:
    separator("ADAPTER: Object adapters (composition)")
    paypal_sdk = LegacyPayPalSdk("client-id", "secret")
    paypal = PayPalAdapter(paypal_sdk)
    acquirer = AcquirerAdapter(ModernAcquirerSdk("api-key"))

    print("Two vendors, one interface. Same calls, different plumbing:\n")
    for gateway in (paypal, acquirer):
        result = gateway.charge(42.50, "USD", "order-100")
        print(f"  {gateway.get_provider_name():>9}: {result}")
        print(f"            approved={result.is_approved} vendor_ref={result.vendor_reference}")

    print("\nUnit conversion happens inside each adapter, invisibly:")
    print(f"  paypal  received cents : {paypal_sdk.calls}")
    print(f"  acquirer received minor: charge 42.50 -> 4250 minor units")

    print("\nDeclines are normalised to one enum:")
    print(f"  paypal   5000.00 -> {paypal.charge(5000.00).status.value}")
    print(f"  acquirer  600.00 -> {acquirer.charge(600.00).status.value}")
    print("  ^ two different vendor rules, one PaymentStatus.DECLINED")

    print("\nRefunds round-trip through the preserved vendor id:")
    charge = paypal.charge(10.00)
    print(f"  charge -> {charge.transaction_id}")
    print(f"  refund -> {paypal.refund(charge.transaction_id)}")

    print("\nFirst-party provider needs no adapter at all:")
    ledger = InHouseLedgerGateway()
    print(f"  {ledger.charge(99.99)}")
    print("  InHouseLedgerGateway implements PaymentGateway directly - the")
    print("  interface is a real boundary, not wrapper tax.")


def demo_error_translation() -> None:
    separator("ADAPTER: Two error conventions, one result type")
    paypal = PayPalAdapter(LegacyPayPalSdk("client-id", "secret"))
    acquirer_sdk = ModernAcquirerSdk("api-key")
    acquirer = AcquirerAdapter(acquirer_sdk)

    print("PayPal reports failures as DATA (an 'err' key):")
    declined = paypal.charge(2000.00)
    print(f"  status={declined.status.value} reason={declined.reason}")

    print("\nThe acquirer reports failures by RAISING:")
    acquirer_sdk.transport_ok = False
    errored = acquirer.charge(2000.00)
    print(f"  status={errored.status.value} reason={errored.reason}")
    acquirer_sdk.transport_ok = True

    print("\nBoth become PaymentStatus.ERROR with a reason string.")
    print("The checkout service never sees an SDK exception type.")


def demo_notification_adapters() -> None:
    separator("ADAPTER: Notification adapters (dict status vs. errno)")
    sms_sender = SmsSenderAdapter(LegacySmsSdk("sid", "token"), sender_id="SHOPT")
    email_sender = SmtpEmailSenderAdapter(SmtpRelay("relay.local"), "no-reply@shop.io")

    print("SMS SDK returns a dict with a status string:")
    print(f"  {sms_sender.send('+919876543210', 'Your order shipped!')}")
    print(f"  bad number -> {sms_sender.send('98765', 'oops')}")

    print("\nSMTP relay returns an integer errno (0 == success):")
    print(f"  {email_sender.send('user@example.com', 'Your order shipped!')}")

    no_sender = SmtpEmailSenderAdapter(SmtpRelay("relay.local"))
    print(f"  no sender configured -> {no_sender.send('user@example.com', 'hi')}")
    print("  ^ errno 250 surfaced as a delivered=False result")


def demo_class_adapter() -> None:
    separator("ADAPTER: Class adapter (inheritance) and its leak")
    class_adapter = PayPalClassAdapter("client-id", "secret")
    print(f"  {class_adapter}")
    print(f"  charge(42.50) -> {class_adapter.charge(42.50)}")
    print("  It satisfies PaymentGateway just like the object adapter.\n")

    print("But it also inherits the adaptee, so the SDK stays reachable:")
    print(f"  MRO: {[c.__name__ for c in type(class_adapter).__mro__[:4]]}")
    print(f"  has charge_cents? {hasattr(class_adapter, 'charge_cents')}")
    print("  A client can bypass the target interface entirely:")
    print(f"  raw SDK call -> {class_adapter.charge_cents(1250, 'USD')}")
    print("  ^ cents in, untyped dict out: no PaymentResult, no enum, no adapter.")

    print("\nCompare the object adapter, which exposes only the target:")
    object_adapter = PayPalAdapter(LegacyPayPalSdk("client-id", "secret"))
    print(f"  public methods: "
          f"{[m for m in dir(object_adapter) if not m.startswith('_')]}")
    print("  charge_cents is unreachable through it -> the leak is sealed.")


def demo_checkout_service() -> None:
    separator("ADAPTER: One checkout service, three providers")
    registry = GatewayRegistry()
    registry.build_default()

    print(f"gateways: {registry.supported_gateways()}")
    print(f"senders:  {registry.supported_senders()}\n")

    checkout = CheckoutService(
        registry.get_gateway("paypal"), registry.get_sender("sms")
    )
    print("CheckoutService was handed a gateway and a sender. It names no vendor.\n")

    for name in registry.supported_gateways():
        service = CheckoutService(registry.get_gateway(name), registry.get_sender("sms"))
        outcome = service.checkout("+919876543210", 42.50, "USD", f"order-{name}")
        flag = "OK " if outcome["ok"] else "ERR"
        print(f"  [{flag}] {name:>9}: {outcome['status']:<9} "
              f"txn={outcome['transaction_id'] or '-':<12} notified={outcome['notified']}")

    print("\nAdd a provider the application never heard of:")
    registry.register_gateway("crypto", InHouseLedgerGateway("crypto-rail"))
    service = CheckoutService(registry.get_gateway("CRYPTO"), registry.get_sender("sms"))
    print(f"  crypto -> {service.checkout('+919876543210', 5.00, 'USD', 'order-x')}")
    print("  (lookup is case-insensitive; CheckoutService was not modified)")

    print("\nDeclines short-circuit before any notification:")
    declining = CheckoutService(registry.get_gateway("paypal"), registry.get_sender("sms"))
    print(f"  {declining.checkout('+919876543210', 5000.00, 'USD', 'order-big')}")

    print("\nUnknown gateway is a lookup error, not an if/elif branch:")
    try:
        registry.get_gateway("bitcoin")
    except KeyError as exc:
        print(f"  KeyError: {exc}")


if __name__ == "__main__":
    print("=" * 62)
    print("  DESIGN PATTERNS - STRUCTURAL: Adapter")
    print("  LLD Implementation Demo")
    print("=" * 62)

    demo_leaky_client()
    demo_object_adapters()
    demo_error_translation()
    demo_notification_adapters()
    demo_class_adapter()
    demo_checkout_service()

    print(f"\n{'=' * 62}")
    print("  All demos completed!")
    print(f"{'=' * 62}")
