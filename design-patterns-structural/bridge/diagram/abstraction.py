"""
Bridge Pattern - ABSTRACTION side of "shape x renderer"

``Shape`` is the abstraction: geometry plus a reference to its renderer.

Each shape knows its own numbers and translates them into renderer
primitives. None of them knows what an SVG is, and no shape contains a
format name. That is the second Bridge in miniature: three shapes and three
formats give nine combinations, and both lists grow without meeting.

``Diagram`` is the composition root. It owns one renderer for the whole
document and binds shapes to it, so a single document is guaranteed to be
internally consistent - you cannot accidentally mix SVG and ASCII in one
canvas, because the canvas decides.
"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod

from .implementor import Renderer


class Shape(ABC):
    """Abstraction: geometry plus a reference to its implementor."""

    def __init__(self, renderer: Renderer) -> None:
        self._renderer = renderer

    @property
    def renderer(self) -> Renderer:
        return self._renderer

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def area(self) -> float:
        ...

    @abstractmethod
    def emit(self) -> None:
        """Translate this shape into renderer primitives. Implementations
        call only ``draw_*`` methods - never anything format-specific."""

    def draw(self) -> str:
        """Standalone rendering: one shape, one document."""
        self._renderer.document_start(self.name())
        self.emit()
        self._renderer.document_end()
        return self._renderer.result()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._renderer!r})"


class Circle(Shape):
    def __init__(self, renderer: Renderer, radius: float) -> None:
        super().__init__(renderer)
        self._radius = radius

    @property
    def radius(self) -> float:
        return self._radius

    def name(self) -> str:
        return "circle"

    def area(self) -> float:
        return math.pi * self._radius**2

    def emit(self) -> None:
        self._renderer.draw_circle(self._radius)


class Rectangle(Shape):
    def __init__(self, renderer: Renderer, width: float, height: float) -> None:
        super().__init__(renderer)
        self._width = width
        self._height = height

    @property
    def width(self) -> float:
        return self._width

    @property
    def height(self) -> float:
        return self._height

    def name(self) -> str:
        return "rectangle"

    def area(self) -> float:
        return self._width * self._height

    def emit(self) -> None:
        self._renderer.draw_rectangle(self._width, self._height)


class Triangle(Shape):
    def __init__(self, renderer: Renderer, base: float, height: float) -> None:
        super().__init__(renderer)
        self._base = base
        self._height = height

    @property
    def base(self) -> float:
        return self._base

    @property
    def height(self) -> float:
        return self._height

    def name(self) -> str:
        return "triangle"

    def area(self) -> float:
        return self._base * self._height / 2

    def emit(self) -> None:
        self._renderer.draw_triangle(self._base, self._height)


class Diagram:
    """Composition root: one renderer, many shapes."""

    def __init__(self, title: str, renderer: Renderer) -> None:
        self._title = title
        self._renderer = renderer
        self._shapes: list[Shape] = []

    @property
    def renderer(self) -> Renderer:
        return self._renderer

    def shapes(self) -> list[Shape]:
        return list(self._shapes)

    def total_area(self) -> float:
        return sum(shape.area() for shape in self._shapes)

    def add_circle(self, radius: float) -> Circle:
        shape = Circle(self._renderer, radius)
        self._shapes.append(shape)
        return shape

    def add_rectangle(self, width: float, height: float) -> Rectangle:
        shape = Rectangle(self._renderer, width, height)
        self._shapes.append(shape)
        return shape

    def add_triangle(self, base: float, height: float) -> Triangle:
        shape = Triangle(self._renderer, base, height)
        self._shapes.append(shape)
        return shape

    def add(self, shape: Shape) -> Shape:
        """Append a shape that was built with this diagram's renderer."""
        if shape.renderer is not self._renderer:
            raise ValueError(
                f"shape was built for {shape.renderer!r}, diagram uses {self._renderer!r}"
            )
        self._shapes.append(shape)
        return shape

    def render(self) -> str:
        self._renderer.document_start(self._title)
        for shape in self._shapes:
            shape.emit()
        self._renderer.document_end()
        return self._renderer.result()
