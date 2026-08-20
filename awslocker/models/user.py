from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    id: str
    name: str
    email: str