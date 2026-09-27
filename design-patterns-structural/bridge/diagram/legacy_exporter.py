"""
The version of "shape x renderer" *without* Bridge

Kept in the project as a counter-example, not as something to use.

One function owns both axes. It takes an untyped list because it cannot
express "some shape", and it branches twice: once per format, once per
shape. Two consequences, both structural rather than stylistic:

- The shape list and the format list are edited in the same place, so each
  new shape adds a branch here *and* a parameter in every signature.
- Because the implementor needs to know each shape, the format code cannot
  be reused for a shape nobody thought of.

Compare with ``diagram/implementor.py``: ``Renderer`` takes primitives and
``Shape`` holds a renderer. This file is what the Bridge removes.
"""
from __future__ import annotations

import json
from typing import Final

from .abstraction import Circle, Rectangle, Shape, Triangle


def export(shapes: list[object], output_format: str) -> str:
    """Format ``shapes`` as ``output_format`` ('svg', 'ascii' or 'json')."""
    if output_format == "svg":
        lines = ["<svg>"]
        for shape in shapes:
            if isinstance(shape, Circle):
                lines.append(f'  <circle r="{shape.radius}" />')
            elif isinstance(shape, Rectangle):
                lines.append(
                    f'  <rect width="{shape.width}" height="{shape.height}" />'
                )
            elif isinstance(shape, Triangle):
                lines.append(f'  <polygon base="{shape.base}" />')
            else:
                raise TypeError(f"unknown shape: {type(shape).__name__}")
        lines.append("</svg>")
        return "\n".join(lines)

    if output_format == "ascii":
        lines = ["ASCII EXPORT"]
        for shape in shapes:
            if isinstance(shape, Circle):
                lines.append("  .-.  (   )  '-")
            elif isinstance(shape, Rectangle):
                lines.append("  +---------+")
            elif isinstance(shape, Triangle):
                lines.append("   /\\")
            else:
                raise TypeError(f"unknown shape: {type(shape).__name__}")
        return "\n".join(lines)

    if output_format == "json":
        payload: list[dict[str, str]] = []
        for shape in shapes:
            if isinstance(shape, Circle):
                payload.append({"kind": "circle"})
            elif isinstance(shape, Rectangle):
                payload.append({"kind": "rectangle"})
            elif isinstance(shape, Triangle):
                payload.append({"kind": "triangle"})
            else:
                raise TypeError(f"unknown shape: {type(shape).__name__}")
        return json.dumps({"shapes": payload})

    raise ValueError(f"unsupported format: {output_format!r}")


def supported_formats() -> list[str]:
    return ["svg", "ascii", "json"]


#: Names of every shape the branch chains above know about. Adding a shape
#: means adding a name here too - the coupling the Bridge removes.
KNOWN_SHAPES: Final[tuple[type[Shape], ...]] = (Circle, Rectangle, Triangle)
