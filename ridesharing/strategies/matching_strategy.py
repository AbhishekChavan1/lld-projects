from abc import ABC, abstractmethod
from typing import List, Optional

from models.driver import Driver
from models.ride_request import RideRequest


class MatchingStrategy(ABC):
    @abstractmethod
    def match(self, ride_request: RideRequest, drivers: List[Driver]) -> Optional[Driver]:
        """Return the best matching driver for the ride request, or None."""
        pass
