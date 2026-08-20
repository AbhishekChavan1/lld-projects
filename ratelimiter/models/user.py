from dataclasses import dataclass
from .tier import Tier


@dataclass(frozen=True)
class User:
    user_id: str
    tier: Tier
    name: str = ""
    email: str = ""