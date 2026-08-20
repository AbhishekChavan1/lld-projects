from typing import List, Optional

from models.driver import Driver
from models.ride_request import RideRequest
from strategies.matching_strategy import MatchingStrategy


class MatchingService:
    """Matches riders to drivers by delegating to a pluggable strategy."""

    def __init__(self, strategy: MatchingStrategy) -> None:
        self.strategy = strategy

    def find_driver(
        self, ride_request: RideRequest, drivers: List[Driver]
    ) -> Optional[Driver]:
        return self.strategy.match(ride_request, drivers)
