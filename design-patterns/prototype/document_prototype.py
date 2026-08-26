"""
Prototype Pattern - Document Prototype (Practical LLD Example)

Creating a copy of an object is expensive (DB query, network call) or complex
(deep graph of nested objects). Instead of re-creating from scratch, clone
an existing instance and modify what's different.

Use cases in LLD:
- Cache: Clone cached response instead of re-fetching
- Document Editor: Duplicate shapes/objects
- Config: Clone default config, modify specific values
"""
from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from typing import Any


class Document(ABC):
    """
    Abstract Prototype interface declaring clone().

    All concrete documents must implement clone() to support
    creating copies of themselves.
    """

    @abstractmethod
    def clone(self) -> Document:
        """Create a deep copy of this document."""
        ...

    @abstractmethod
    def get_content(self) -> str:
        ...


class ReportDocument(Document):
    """
    Concrete Prototype - Report Document.

    Demonstrates the prototype pattern:
    1. Expensive DB load happens ONCE in __init__
    2. clone() copies the in-memory object (cheap)
    3. Cloned documents are independent (deep copy)
    """

    def __init__(self, title: str, author: str) -> None:
        self.title = title
        self.author = author
        self.sections: list[str] = []
        self.metadata: dict[str, Any] = {}
        self._load_from_database()

    def _load_from_database(self) -> None:
        """Simulated expensive database load."""
        print(f"  [DB] Loading report template for '{self.title}'...")
        self.sections = ["Executive Summary", "Findings", "Recommendations"]
        self.metadata = {"template": "annual", "version": "v2"}

    def clone(self) -> ReportDocument:
        """Create a deep copy - no DB load required."""
        print(f"  [Clone] Copying '{self.title}' (no DB load)")
        return copy.deepcopy(self)

    def get_content(self) -> str:
        return f"Report: {self.title} by {self.author}"

    def set_title(self, title: str) -> None:
        self.title = title

    def add_section(self, section: str) -> None:
        self.sections.append(section)

    def set_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def __repr__(self) -> str:
        return (
            f"ReportDocument(title='{self.title}', author='{self.author}', "
            f"sections={self.sections}, metadata={self.metadata})"
        )
