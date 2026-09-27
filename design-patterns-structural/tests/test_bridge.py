"""
Bridge Pattern tests

Two claims are worth more than the behaviour checks below:

1. The abstraction *composes* its implementor (no cross-hierarchy
   inheritance), and the implementor's signature never mentions the
   abstraction. Checked with ``inspect``.
2. Both axes stay open. A new message and a new channel defined *in this
   test file* work together without editing the project.

The behavioural tests then walk the 3x3 grid in both examples.
"""
from __future__ import annotations

import ast
import inspect
import json
from collections.abc import Callable

import pytest

from bridge.diagram import (
    AsciiRenderer,
    Circle,
    Diagram,
    JsonGeometryRenderer,
    Rectangle,
    Renderer,
    Shape,
    SvgRenderer,
    Triangle,
)
from bridge.diagram import legacy_exporter
from bridge.notification import (
    Channel,
    ChannelKind,
    DeliveryReceipt,
    EmailChannel,
    Message,
    NotificationCenter,
    OtpMessage,
    OrderShippedMessage,
    PaymentReceiptMessage,
    PushChannel,
    SmsChannel,
)
from bridge import demo as bridge_demo

# --------------------------------------------------------------------------
# Fakes defined here, not in the project, to prove the axes are open
# --------------------------------------------------------------------------


class FaxChannel(Channel):
    """A fourth implementor written without touching the project."""

    def kind(self) -> ChannelKind:
        return ChannelKind.SMS

    def deliver(self, recipient: str, subject: str, body: str) -> DeliveryReceipt:
        return DeliveryReceipt(
            channel=self.kind(),
            recipient=recipient,
            message_id="fax-1",
            subject_used=bool(subject),
            body_length=len(body),
            delivered=recipient.startswith("+"),
            detail="via modem",
        )


class MaintenanceNotice(Message):
    """A fourth abstraction written without touching the project."""

    def subject(self) -> str:
        return "Scheduled maintenance"

    def body(self) -> str:
        return "We will be down at 02:00 UTC for two hours."


class BrailleRenderer(Renderer):
    """A fourth implementor that reuses the existing primitives only."""

    def name(self) -> str:
        return "braille"

    def document_start(self, title: str) -> None:
        self._title = title

    def draw_circle(self, radius: float) -> None:
        self._lines.append(f"circle {radius:g}")

    def draw_rectangle(self, width: float, height: float) -> None:
        self._lines.append(f"rect {width:g}x{height:g}")

    def draw_triangle(self, base: float, height: float) -> None:
        self._lines.append(f"triangle {base:g}/{height:g}")

    def document_end(self) -> None:
        return None

    def result(self) -> str:
        return f"{self._title}\n" + "\n".join(self._lines)

    def __init__(self) -> None:
        self._title = ""
        self._lines: list[str] = []


class Hexagon(Shape):
    """A fourth abstraction. Note it needed no new renderer method."""

    def __init__(self, renderer: Renderer, side: float) -> None:
        super().__init__(renderer)
        self._side = side

    def name(self) -> str:
        return "hexagon"

    def area(self) -> float:
        return 1.5 * 2**0.5 * self._side**2

    def emit(self) -> None:
        # Reuses draw_triangle, the same compromise a real implementor makes.
        self._renderer.draw_triangle(self._side, self._side)


CHANNELS: list[type[Channel]] = [SmsChannel, EmailChannel, PushChannel]
MESSAGES: list[type[Message]] = [OtpMessage, OrderShippedMessage, PaymentReceiptMessage]
RENDERERS: list[type[Renderer]] = [SvgRenderer, AsciiRenderer, JsonGeometryRenderer]
SHAPES: list[type[Shape]] = [Circle, Rectangle, Triangle]

VALID_RECIPIENTS = {
    "SmsChannel": "+919876543210",
    "EmailChannel": "buyer@shop.io",
    "PushChannel": "device-abc123",
}


# --------------------------------------------------------------------------
# Message x Channel - structure
# --------------------------------------------------------------------------


class TestMessageChannelStructure:
    def test_message_composes_its_implementor(self) -> None:
        assert issubclass(Message, object)
        assert not issubclass(Message, Channel)
        assert not issubclass(Channel, Message)

    def test_message_stores_channel_instance(self) -> None:
        message = OtpMessage(SmsChannel(), "123456")
        assert isinstance(message.channel, SmsChannel)

    def test_implementor_signature_never_mentions_message(self) -> None:
        """``Channel.deliver`` takes three plain strings. A Message parameter
        anywhere in the implementor would invert the dependency."""
        params = inspect.signature(Channel.deliver).parameters
        assert list(params) == ["self", "recipient", "subject", "body"]
        assert all(
            param.annotation in ("str", str) for name, param in params.items()
            if name != "self"
        )

    def test_no_combination_subclasses_exist(self) -> None:
        """A Bridge has no SmsOtpMessage / SvgCircle / ... anywhere."""
        offenders = [
            f"{cls.__module__}.{cls.__name__}"
            for cls in (*MESSAGES, *SHAPES, *CHANNELS, *RENDERERS)
            if any(
                token in cls.__name__
                for token in ("Sms", "Email", "Push", "Svg", "Ascii", "Json")
            )
            and not issubclass(cls, (SmsChannel, EmailChannel, PushChannel,
                                     SvgRenderer, AsciiRenderer, JsonGeometryRenderer))
        ]
        assert offenders == []

    def test_send_is_a_template_method(self) -> None:
        assert "send" in Message.__dict__
        assert "send" not in OtpMessage.__dict__
        assert "deliver" not in OtpMessage.__dict__


# --------------------------------------------------------------------------
# Message x Channel - behaviour
# --------------------------------------------------------------------------


class TestMessageChannelMatrix:
    @pytest.mark.parametrize("channel_cls", CHANNELS)
    @pytest.mark.parametrize("message_cls", MESSAGES)
    def test_every_pair_delivers(
        self, channel_cls: type[Channel], message_cls: type[Message]
    ) -> None:
        channel = channel_cls()
        if message_cls is OtpMessage:
            message: Message = OtpMessage(channel, "739104")
        elif message_cls is OrderShippedMessage:
            message = OrderShippedMessage(channel, "A-1", "BlueDart")
        else:
            message = PaymentReceiptMessage(channel, "INR 10.00", "4242")

        receipt = message.send(VALID_RECIPIENTS[channel_cls.__name__])
        assert receipt.delivered
        assert receipt.channel is channel.kind()
        assert receipt.message_id
        assert receipt.body_length > 0

    def test_matrix_is_three_by_three_from_six_classes(self) -> None:
        assert len(MESSAGES) * len(CHANNELS) == 9
        assert len(MESSAGES) + len(CHANNELS) == 6

    def test_subject_is_ignored_over_sms(self) -> None:
        receipt = OtpMessage(SmsChannel(), "739104").send("+919876543210")
        assert receipt.subject_used is False

    def test_subject_is_kept_over_email(self) -> None:
        receipt = OtpMessage(EmailChannel(), "739104").send("buyer@shop.io")
        assert receipt.subject_used is True

    def test_sms_folds_subject_into_body(self) -> None:
        message = OrderShippedMessage(SmsChannel(), "A-4471", "BlueDart")
        with_subject = SmsChannel().deliver("+919876543210", "S", "B").body_length
        without = SmsChannel().deliver("+919876543210", "", "B").body_length
        assert with_subject > without
        assert message.subject() != ""

    def test_each_channel_rejects_bad_recipients_on_its_own_terms(self) -> None:
        assert SmsChannel().deliver("9876543210", "s", "b").delivered is False
        assert EmailChannel().deliver("buyer@shop", "s", "b").delivered is False
        assert PushChannel().deliver("buyer@shop.io", "s", "b").delivered is False

    def test_sms_refuses_over_length_body(self) -> None:
        channel = SmsChannel()
        long_body = "x" * (channel.max_body + 1)
        receipt = channel.deliver("+919876543210", "", long_body)
        assert receipt.delivered is False
        assert "characters" in receipt.detail

    def test_message_ids_increment(self) -> None:
        channel = SmsChannel()
        first = channel.deliver("+919876543210", "a", "b")
        second = channel.deliver("+919876543210", "a", "b")
        assert first.message_id != second.message_id

    def test_receipt_repr_is_readable(self) -> None:
        receipt = SmsChannel().deliver("+919876543210", "a", "b")
        assert repr(receipt) == "DeliveryReceipt(sms, +919876543210, sent)"

    def test_describe_and_repr_name_the_channel(self) -> None:
        message = OtpMessage(EmailChannel(), "1")
        assert message.describe() == "OtpMessage -> email"
        assert "EmailChannel" in repr(message)

    def test_max_body_differs_per_channel(self) -> None:
        lengths = {cls.__name__: cls().max_body for cls in CHANNELS}
        assert len(set(lengths.values())) == 3


class TestNewImplementorAndAbstraction:
    def test_new_channel_works_with_existing_messages(self) -> None:
        for message_cls in MESSAGES:
            message = (
                OtpMessage(FaxChannel(), "1")
                if message_cls is OtpMessage
                else OrderShippedMessage(FaxChannel(), "A", "C")
            )
            assert message.send("+919876543210").detail == "via modem"

    def test_new_message_works_with_existing_channels(self) -> None:
        for channel_cls in CHANNELS:
            receipt = MaintenanceNotice(channel_cls()).send(
                VALID_RECIPIENTS[channel_cls.__name__]
            )
            assert receipt.delivered

    def test_new_message_subclasses_only_need_subject_and_body(self) -> None:
        """Message declares exactly two abstract methods, so a new
        abstraction is a five-line class."""
        assert Message.__abstractmethods__ == frozenset({"subject", "body"})
        assert MaintenanceNotice.__abstractmethods__ == frozenset()


class TestNotificationCenter:
    def test_register_and_lookup(self) -> None:
        center = NotificationCenter()
        center.register("SMS", SmsChannel())
        assert isinstance(center.channel("sms"), SmsChannel)
        assert center.names() == ["sms"]

    def test_center_just_delegates_to_the_message(self) -> None:
        """The center adds no behaviour: its receipt is the message's."""
        center = NotificationCenter()
        center.register("sms", SmsChannel())
        message = OtpMessage(center.channel("sms"), "1")

        first = center.send(message, "+919876543210")
        second = message.send("+919876543210")
        assert first.channel is second.channel
        assert first.delivered is second.delivered
        assert second.message_id.endswith("00002")

    def test_unknown_channel_raises(self) -> None:
        center = NotificationCenter()
        center.register("sms", SmsChannel())
        with pytest.raises(KeyError):
            center.channel("carrier-pigeon")


# --------------------------------------------------------------------------
# Shape x Renderer - structure
# --------------------------------------------------------------------------


class TestShapeRendererStructure:
    def test_shape_composes_its_implementor(self) -> None:
        assert not issubclass(Shape, Renderer)
        assert not issubclass(Renderer, Shape)

    def test_renderer_interface_is_primitives_only(self) -> None:
        """No renderer method may accept a Shape. This is the rule that
        keeps new shapes free of renderer changes."""
        for name, member in inspect.getmembers(Renderer, inspect.isfunction):
            if name.startswith("_"):
                continue
            hints = list(inspect.signature(member).parameters)
            assert "shape" not in hints, f"{name} takes a shape"

    def test_renderer_module_never_references_a_shape(self) -> None:
        """Parsed, not grepped: a mention in the docstring is fine, a
        reference in code is not."""
        module = inspect.getmodule(Renderer)
        assert module is not None
        tree = ast.parse(inspect.getsource(module))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "abstraction":
                pytest.fail(f"implementor imports the abstraction: {node.module}")
            if isinstance(node, ast.ClassDef) and any(
                base.id == "Shape" for base in node.bases if isinstance(base, ast.Name)
            ):
                pytest.fail(f"{node.name} inherits from Shape")
            if isinstance(node, ast.Name) and node.id in {"Shape", "Circle", "Rectangle", "Triangle"}:
                pytest.fail(f"implementor references {node.id} in code")

    def test_shapes_only_call_draw_primitives(self) -> None:
        for shape_cls in SHAPES:
            emit = inspect.getsource(shape_cls.emit)
            for name in ("document_start", "document_end", "result", "name"):
                assert name not in emit
            assert "draw_" in emit

    def test_renderer_declares_every_primitive(self) -> None:
        source = inspect.getsource(Renderer)
        for primitive in ("draw_circle", "draw_rectangle", "draw_triangle"):
            assert primitive in source


# --------------------------------------------------------------------------
# Shape x Renderer - behaviour
# --------------------------------------------------------------------------


class TestGeometry:
    def test_circle_area(self) -> None:
        assert Circle(SvgRenderer(), 2.0).area() == pytest.approx(12.566, rel=1e-3)

    def test_rectangle_area(self) -> None:
        assert Rectangle(SvgRenderer(), 4.0, 2.5).area() == pytest.approx(10.0)

    def test_triangle_area(self) -> None:
        assert Triangle(SvgRenderer(), 6.0, 4.0).area() == pytest.approx(12.0)

    def test_area_is_format_independent(self) -> None:
        """Same geometry, same number, whatever the renderer is."""
        areas = [
            Triangle(renderer_cls(), 2.0, 3.0).area() for renderer_cls in RENDERERS
        ]
        assert areas == [pytest.approx(3.0)] * len(RENDERERS)


class TestRenderers:
    def test_svg_contains_one_element_per_shape(self) -> None:
        diagram = Diagram("d", SvgRenderer())
        diagram.add_circle(10.0)
        diagram.add_rectangle(20.0, 10.0)
        diagram.add_triangle(30.0, 15.0)
        svg = diagram.render()
        assert svg.count("<circle") == 1
        assert svg.count("<rect") == 1
        assert svg.count("<polygon") == 1
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_ascii_is_not_markup(self) -> None:
        diagram = Diagram("d", AsciiRenderer())
        diagram.add_circle(10.0)
        diagram.add_rectangle(20.0, 10.0)
        diagram.add_triangle(30.0, 15.0)
        text = diagram.render()
        assert "<" not in text
        assert "circle r=10" in text
        assert "rect 20x10" in text

    def test_json_is_machine_readable(self) -> None:
        diagram = Diagram("shop", JsonGeometryRenderer())
        diagram.add_circle(10.0)
        diagram.add_rectangle(20.0, 10.0)
        payload = json.loads(diagram.render())
        assert payload["title"] == "shop"
        assert payload["primitives"] == [
            {"kind": "circle", "radius": 10.0},
            {"kind": "rectangle", "width": 20.0, "height": 10.0},
        ]

    def test_renderer_names_are_unique(self) -> None:
        assert len({cls().name() for cls in RENDERERS}) == 3

    def test_renderer_repr_shows_name(self) -> None:
        assert repr(SvgRenderer()) == "SvgRenderer(name='svg')"


class TestDiagram:
    def test_total_area_sums_shapes(self) -> None:
        diagram = Diagram("d", SvgRenderer())
        diagram.add_rectangle(2.0, 3.0)
        diagram.add_rectangle(4.0, 5.0)
        assert diagram.total_area() == pytest.approx(26.0)

    def test_shapes_list_is_a_copy(self) -> None:
        diagram = Diagram("d", SvgRenderer())
        diagram.add_circle(1.0)
        shapes = diagram.shapes()
        shapes.clear()
        assert len(diagram.shapes()) == 1

    def test_rejects_shape_from_another_renderer(self) -> None:
        diagram = Diagram("d", SvgRenderer())
        stray = Circle(AsciiRenderer(), 1.0)
        with pytest.raises(ValueError, match="built for"):
            diagram.add(stray)

    def test_accepts_matching_shape(self) -> None:
        renderer = SvgRenderer()
        diagram = Diagram("d", renderer)
        diagram.add(Circle(renderer, 1.0))
        assert len(diagram.shapes()) == 1

    def test_standalone_shape_draws_a_full_document(self) -> None:
        svg = Circle(SvgRenderer(), 5.0).draw()
        assert svg.startswith("<svg")
        assert "<circle" in svg
        assert svg.endswith("</svg>")


class TestNewShapeAndRenderer:
    def test_new_shape_needs_no_renderer_change(self) -> None:
        for renderer_cls in RENDERERS:
            hexagon = Hexagon(renderer_cls(), 2.0)
            rendered = hexagon.draw()
            assert rendered
            assert "triangle" in rendered or "polygon" in rendered or "circle" in rendered

    def test_new_renderer_needs_no_shape_change(self) -> None:
        """BrailleRenderer was written above without touching Circle,
        Rectangle or Triangle. Prove it drives all three primitives."""
        for add, expected in (
            (lambda d: d.add_circle(7.0), "circle 7"),
            (lambda d: d.add_rectangle(3.0, 4.0), "rect 3x4"),
            (lambda d: d.add_triangle(5.0, 6.0), "triangle 5/6"),
        ):
            diagram = Diagram("d", BrailleRenderer())
            add(diagram)
            assert expected in diagram.render()

    def test_new_shape_still_reports_geometry(self) -> None:
        assert Hexagon(SvgRenderer(), 2.0).area() == pytest.approx(1.5 * 2**0.5 * 4)


# --------------------------------------------------------------------------
# The counter-example
# --------------------------------------------------------------------------


class TestLegacyExporter:
    def test_it_still_works_for_known_shapes(self) -> None:
        shapes: list[object] = [
            Circle(SvgRenderer(), 1.0),
            Rectangle(SvgRenderer(), 2.0, 3.0),
            Triangle(SvgRenderer(), 4.0, 5.0),
        ]
        assert "<circle" in legacy_exporter.export(shapes, "svg")
        assert "circle" in legacy_exporter.export(shapes, "json")
        assert "ASCII" in legacy_exporter.export(shapes, "ascii")

    def test_it_cannot_handle_an_unknown_shape(self) -> None:
        with pytest.raises(TypeError):
            legacy_exporter.export([Hexagon(SvgRenderer(), 1.0)], "svg")

    def test_it_cannot_handle_an_unknown_format(self) -> None:
        with pytest.raises(ValueError):
            legacy_exporter.export([], "pdf")

    def test_its_signature_is_untyped_by_necessity(self) -> None:
        """``list[object]`` is the smell: the function cannot say 'some
        shape', which is exactly why it needs isinstance chains."""
        hints = inspect.signature(legacy_exporter.export).parameters
        assert hints["shapes"].annotation == "list[object]"

    def test_it_branches_on_every_shape(self) -> None:
        source = inspect.getsource(legacy_exporter.export)
        for shape_cls in SHAPES:
            assert f"isinstance(shape, {shape_cls.__name__})" in source

    def test_known_shapes_tuple_is_a_coupling_inventory(self) -> None:
        assert set(legacy_exporter.KNOWN_SHAPES) == set(SHAPES)
        assert legacy_exporter.supported_formats() == ["svg", "ascii", "json"]


# --------------------------------------------------------------------------
# Demo
# --------------------------------------------------------------------------


class TestBridgeDemo:
    def test_demo_runs(self, capsys: pytest.CaptureFixture[str]) -> None:
        bridge_demo.run_all()
        out = capsys.readouterr().out
        assert "MESSAGE x CHANNEL" in out
        assert "SHAPE x RENDERER" in out

    def test_center_helper_registers_three_channels(self) -> None:
        assert bridge_demo.build_center().names() == ["email", "push", "sms"]

    def test_builders_cover_every_message(self) -> None:
        builders: list[Callable[[Channel], Message]] = [
            build for _, build in bridge_demo.message_builders()
        ]
        produced = {type(build(SmsChannel())) for build in builders}
        assert produced == set(MESSAGES)
