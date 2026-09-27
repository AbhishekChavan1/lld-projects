"""
Bridge Pattern - runnable demonstration

    python -m bridge.demo

Two axes, one story each:

1. message x channel - three message classes, three channel classes, and
   the 3x3 grid they cover without any combination subclass.
2. shape x renderer - the same grid, plus the branching counter-example it
   replaces.
"""
from __future__ import annotations

from collections.abc import Callable

from .diagram import (
    AsciiRenderer,
    Circle,
    Diagram,
    JsonGeometryRenderer,
    Rectangle,
    SvgRenderer,
    Triangle,
)
from .diagram.legacy_exporter import export, supported_formats
from .notification import (
    Channel,
    EmailChannel,
    Message,
    NotificationCenter,
    OtpMessage,
    OrderShippedMessage,
    PaymentReceiptMessage,
    PushChannel,
    SmsChannel,
)


def banner(title: str) -> None:
    print(f"\n{'-' * 66}")
    print(f"  {title}")
    print(f"{'-' * 66}")


def build_center() -> NotificationCenter:
    center = NotificationCenter()
    center.register("sms", SmsChannel())
    center.register("email", EmailChannel())
    center.register("push", PushChannel())
    return center


def message_builders() -> list[tuple[str, Callable[[Channel], Message]]]:
    """(label, builder) pairs. A builder takes a Channel, which is why this
    same list pairs with every registered channel."""
    return [
        ("otp", lambda channel: OtpMessage(channel, "739104")),
        (
            "shipped",
            lambda channel: OrderShippedMessage(channel, "A-4471", "BlueDart", eta_days=2),
        ),
        ("receipt", lambda channel: PaymentReceiptMessage(channel, "INR 1299.00", "4242")),
    ]


def demo_message_channel() -> None:
    banner("MESSAGE x CHANNEL")
    print("Message holds a Channel. Channel methods take strings, never a Message.")
    print("A 3x3 grid of combinations costs six classes, not nine.\n")

    center = build_center()
    recipients = {"sms": "+919876543210", "email": "buyer@shop.io", "push": "device-abc123"}

    for channel_name in center.names():
        channel = center.channel(channel_name)
        print(f"[{channel_name}]  {channel!r}  max_body={channel.max_body}")
        for label, build in message_builders():
            message = build(channel)
            receipt = center.send(message, recipients[channel_name])
            status = "sent" if receipt.delivered else "failed"
            print(
                f"    {label:<8} {status:<6} id={receipt.message_id} "
                f"len={receipt.body_length:<3} {receipt.detail}"
            )
        print()

    print("\nChannels disagree about the same three strings, and no message cares:")
    phone = "+919876543210"
    sms_receipt = PaymentReceiptMessage(center.channel("sms"), "INR 1299.00", "4242")
    email_receipt = PaymentReceiptMessage(center.channel("email"), "INR 1299.00", "4242")
    push_receipt = PaymentReceiptMessage(center.channel("push"), "INR 1299.00", "4242")
    for message, recipient in (
        (sms_receipt, phone),
        (email_receipt, "buyer@shop.io"),
        (push_receipt, "device-abc123"),
    ):
        sent = message.send(recipient)
        print(
            f"    {sent.channel.value:<6} subject_used={str(sent.subject_used):<5} "
            f"delivered={str(sent.delivered):<5} {sent.detail}"
        )

    print("\nEach channel validates a recipient by its own rules:")
    otp_over_email = OtpMessage(center.channel("email"), "739104")
    otp_over_sms = OtpMessage(center.channel("sms"), "739104")
    for message, bad in (
        (otp_over_email, "buyer@shop"),
        (otp_over_email, "no-at-sign"),
        (otp_over_sms, "9876543210"),
    ):
        receipt = message.send(bad)
        print(
            f"    {receipt.channel.value:<6} {bad:<14} "
            f"delivered={receipt.delivered} {receipt.detail}"
        )


def demo_shape_renderer() -> None:
    banner("SHAPE x RENDERER")
    print("Shape holds a Renderer. The renderer's interface is primitives only:")
    print("draw_circle(radius), draw_rectangle(w, h), draw_triangle(b, h) -")
    print("so a new shape needs no new renderer method, and vice versa.\n")

    renderers = [SvgRenderer(), AsciiRenderer(), JsonGeometryRenderer()]

    circle = Circle(SvgRenderer(), 40.0)
    rectangle = Rectangle(SvgRenderer(), 90.0, 45.0)
    triangle = Triangle(SvgRenderer(), 60.0, 50.0)
    print("Geometry belongs to the shape, and is identical for every format:")
    print(f"    {circle.name():<10} area={circle.area():.1f}")
    print(f"    {rectangle.name():<10} area={rectangle.area():.1f}")
    print(f"    {triangle.name():<10} area={triangle.area():.1f}")
    print(f"    total       area={circle.area() + rectangle.area() + triangle.area():.1f}")

    print("\nOne set of shapes, three documents, zero edits to the shapes:")
    for renderer in renderers:
        diagram = Diagram(f"from {renderer.name()}", renderer)
        diagram.add_circle(40.0)
        diagram.add_rectangle(90.0, 45.0)
        diagram.add_triangle(60.0, 50.0)
        body = diagram.render()
        preview = body.splitlines()[0] if body else ""
        print(f"    {renderer.name():<6} {len(body):>3} chars  first line: {preview}")

    print("\nA single shape renders standalone through the same primitives:")
    print("    " + Circle(SvgRenderer(), 20.0).draw().splitlines()[-2].strip())

    print("\nThe counter-example: one function owning both axes.")
    shapes: list[object] = [Circle(SvgRenderer(), 20.0), Rectangle(SvgRenderer(), 10.0, 5.0)]
    for output_format in supported_formats():
        rendered = export(shapes, output_format)
        print(f"    {output_format:<6} {len(rendered.splitlines())} lines, "
              f"branches on shape and format")


def demo_shape_renderer_detail() -> None:
    banner("SHAPE x RENDERER - one full document")
    diagram = Diagram("shop floor plan", SvgRenderer())
    diagram.add_circle(30.0)
    diagram.add_rectangle(120.0, 60.0)
    diagram.add_triangle(50.0, 40.0)
    print(diagram.render())


def run_all() -> None:
    """Every Bridge demo, in teaching order."""
    demo_message_channel()
    demo_shape_renderer()
    demo_shape_renderer_detail()


if __name__ == "__main__":
    run_all()
    print(f"\n{'-' * 66}")
    print("  Bridge demos completed!")
    print(f"{'-' * 66}")
