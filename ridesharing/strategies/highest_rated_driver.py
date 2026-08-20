from typing import List, Optional

from models.driver import Driver
from models.ride_request import RideRequest
from strategies.matching_strategy import MatchingStrategy


class HighestRatedDriverStrategy(MatchingStrategy):
    def match(self, ride_request: RideRequest, drivers: List[Driver]) -> Optional[Driver]:
        candidates = [d for d in drivers if d.is_available and d.location is not None]
        if not candidates:
            return None
        return max(candidates, key=lambda driver: driver.rating)
