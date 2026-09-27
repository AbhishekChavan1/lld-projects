"""
Design Patterns - Structural Patterns (LLD)

Entry point for the whole project. Each pattern owns its demo; this file
only decides what to run.

    python main.py            # every pattern
    python main.py bridge     # one pattern
    python -m pytest          # the tests

Patterns:
- Adapter: third-party payment/notification SDKs behind our interfaces
- Bridge: two hierarchies that vary independently (message x channel,
  shape x renderer)
"""
from __future__ import annotations

import sys
from collections.abc import Callable

from adapter import demo as adapter_demo
from bridge import demo as bridge_demo

PATTERNS: dict[str, Callable[[], None]] = {
    "adapter": adapter_demo.run_all,
    "bridge": bridge_demo.run_all,
}


def banner(title: str) -> None:
    print(f"\n{'':=^62}")
    print(f"{title:^62}")
    print(f"{'':=^62}")


def main(argv: list[str]) -> int:
    requested = [arg.lower() for arg in argv[1:]]
    unknown = [name for name in requested if name not in PATTERNS]
    if unknown:
        print(f"Unknown pattern(s): {', '.join(unknown)}")
        print(f"Available: {', '.join(sorted(PATTERNS))}")
        return 2
    if not requested:
        requested = sorted(PATTERNS)

    for name in requested:
        banner(f"DESIGN PATTERNS - STRUCTURAL: {name.upper()}")
        PATTERNS[name]()

    print(f"\n{'':=^62}")
    print(f"  Completed: {', '.join(requested)}")
    print(f"{'':=^62}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
