from models.location import Location
from strategies.pricing_strategy import PricingStrategy


class BasicPricingStrategy(PricingStrategy):
    def __init__(self, rate_per_km: float = 10.0, base_fare: float = 2.0) -> None:
        self.rate_per_km = rate_per_km
        self.base_fare = base_fare

    def calculate_fare(self, pickup: Location, dropoff: Location) -> float:
        distance = pickup.distance_to(dropoff)
        return round(self.base_fare + distance * self.rate_per_km, 2)
