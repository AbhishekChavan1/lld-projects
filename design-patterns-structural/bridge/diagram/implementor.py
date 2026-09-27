"""
Bridge Pattern - IMPLEMENTOR side of "shape x renderer"

``Renderer`` is the implementor: it turns *drawing primitives* into an
output format. It does not know a shape exists.

The interface is deliberately low-level - ``draw_circle(radius)``,
``draw_rectangle(width, height)`` - rather than ``draw(shape)``. That
choice is what makes the abstraction independent: a renderer written once
can serve every shape that exists now and every shape added later, and a
new shape never needs a new renderer method.

If instead the implementor took ``Shape`` objects, we would be back to a
single hierarchy that grows a method per format - the mistake
``legacy_exporter.py`` makes deliberately.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod


class Renderer(ABC):
    """Implementor: primitives in, formatted document out."""

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def document_start(self, title: str) -> None:
        ...

    @abstractmethod
    def draw_circle(self, radius: float) -> None:
        ...

    @abstractmethod
    def draw_rectangle(self, width: float, height: float) -> None:
        ...

    @abstractmethod
    def draw_triangle(self, base: float, height: float) -> None:
        ...

    @abstractmethod
    def document_end(self) -> None:
        ...

    @abstractmethod
    def result(self) -> str:
        """The document accumulated so far."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name()!r})"


class SvgRenderer(Renderer):
    """Self-contained markup."""

    def __init__(self, size: int = 320) -> None:
        self._size = size
        self._parts: list[str] = []
        self._title = ""

    def name(self) -> str:
        return "svg"

    def document_start(self, title: str) -> None:
        self._title = title
        self._parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 '
            f'{self._size} {self._size}" width="{self._size}" '
            f'height="{self._size}">',
            f"  <title>{self._title}</title>",
        ]

    def draw_circle(self, radius: float) -> None:
        center = self._size / 2
        self._parts.append(
            f'  <circle cx="{center}" cy="{center}" r="{radius}" '
            f'fill="none" stroke="black" />'
        )

    def draw_rectangle(self, width: float, height: float) -> None:
        x = (self._size - width) / 2
        y = (self._size - height) / 2
        self._parts.append(
            f'  <rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'fill="none" stroke="black" />'
        )

    def draw_triangle(self, base: float, height: float) -> None:
        left = (self._size - base) / 2
        top = (self._size - height) / 2
        points = f"{left},{self._size - top} {left + base / 2},{top} {left + base},{self._size - top}"
        self._parts.append(f'  <polygon points="{points}" fill="none" stroke="black" />')

    def document_end(self) -> None:
        self._parts.append("</svg>")

    def result(self) -> str:
        return "\n".join(self._parts)


class AsciiRenderer(Renderer):
    """Terminal output. Draws a legend plus a fixed-width art block, so the
    format is visibly different from the markup one."""

    WIDTH = 40

    def __init__(self) -> None:
        self._lines: list[str] = []
        self._title = ""

    def name(self) -> str:
        return "ascii"

    def document_start(self, title: str) -> None:
        self._title = title
        self._lines = [title, "=" * min(len(title), self.WIDTH), ""]

    def _record(self, text: str, art: list[str]) -> None:
        self._lines.append(text)
        self._lines.extend(art)

    def draw_circle(self, radius: float) -> None:
        self._record(f"circle r={radius:g}", ["  .-.", " (   )", "  '-'"])

    def draw_rectangle(self, width: float, height: float) -> None:
        art = ["  " + "+" + "-" * 10 + "+", "  |" + " " * 10 + "|", "  " + "+" + "-" * 10 + "+"]
        self._record(f"rect {width:g}x{height:g}", art)

    def draw_triangle(self, base: float, height: float) -> None:
        art = ["   /\\", "  /  \\", " /____\\"]
        self._record(f"triangle b={base:g} h={height:g}", art)

    def document_end(self) -> None:
        self._lines.append("")

    def result(self) -> str:
        return "\n".join(self._lines)


class JsonGeometryRenderer(Renderer):
    """Machine-readable output for a downstream client."""

    def __init__(self) -> None:
        self._primitives: list[dict[str, float | str]] = []
        self._title = ""

    def name(self) -> str:
        return "json"

    def document_start(self, title: str) -> None:
        self._title = title
        self._primitives = []

    def draw_circle(self, radius: float) -> None:
        self._primitives.append({"kind": "circle", "radius": radius})

    def draw_rectangle(self, width: float, height: float) -> None:
        self._primitives.append({"kind": "rectangle", "width": width, "height": height})

    def draw_triangle(self, base: float, height: float) -> None:
        self._primitives.append({"kind": "triangle", "base": base, "height": height})

    def document_end(self) -> None:
        """No closing work: JSON is a value, not a stream."""

    def result(self) -> str:
        return json.dumps({"title": self._title, "primitives": self._primitives}, indent=2)
