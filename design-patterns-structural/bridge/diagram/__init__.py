"""
Bridge Pattern - "shape x renderer"

``Shape`` (abstraction) x ``Renderer`` (implementor).
"""
from .abstraction import Circle, Diagram, Rectangle, Shape, Triangle
from .implementor import AsciiRenderer, JsonGeometryRenderer, Renderer, SvgRenderer

__all__ = [
    "AsciiRenderer",
    "Circle",
    "Diagram",
    "JsonGeometryRenderer",
    "Rectangle",
    "Renderer",
    "Shape",
    "SvgRenderer",
    "Triangle",
]
