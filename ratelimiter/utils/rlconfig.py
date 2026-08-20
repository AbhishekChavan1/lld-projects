from dataclasses import dataclass

@dataclass(frozen=True)
class RLConfig:
    window_size: float
    max_requests: int
