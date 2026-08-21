from enum import Enum


class BookStatus(Enum):
    AVAILABLE = "Available"
    LOANED = "Loaned"
    RESERVED = "Reserved"
