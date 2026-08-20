from typing import List, Optional

from models.driver import Driver
from models.location import Location
from models.ride_request import RideRequest
from strategies.matching_strategy import MatchingStrategy


class CheapestDriverStrategy(MatchingStrategy):
    def __init__(self, cost_per_km: float = 1.0) -> None:
        self.cost_per_km = cost_per_km

    def match(self, ride_request: RideRequest, drivers: List[Driver]) -> Optional[Driver]:
        cheapest_driver: Optional[Driver] = None
        min_cost = float("inf")

        for driver in drivers:
            if not driver.is_available or driver.location is None:
                continue
            cost = self.calculate_cost(ride_request.pickup_location, driver.location)
            if cost < min_cost:
                min_cost = cost
                cheapest_driver = driver

        return cheapest_driver

    def calculate_cost(self, location1: Location, location2: Location) -> float:
        """Estimate the pickup cost based on distance."""
        distance = location1.distance_to(location2)
        return distance * self.cost_per_km
