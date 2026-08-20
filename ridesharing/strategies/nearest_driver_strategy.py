from typing import List, Optional

from models.driver import Driver
from models.ride_request import RideRequest
from strategies.matching_strategy import MatchingStrategy


class NearestDriverStrategy(MatchingStrategy):
    def match(self, ride_request: RideRequest, drivers: List[Driver]) -> Optional[Driver]:
        nearest_driver: Optional[Driver] = None
        min_distance = float("inf")

        for driver in drivers:
            if not driver.is_available or driver.location is None:
                continue
            distance = ride_request.pickup_location.distance_to(driver.location)
            if distance < min_distance:
                min_distance = distance
                nearest_driver = driver

        return nearest_driver
