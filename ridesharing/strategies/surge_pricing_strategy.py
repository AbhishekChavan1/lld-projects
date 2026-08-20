from models.location import Location
from strategies.basic_pricing_strategy import BasicPricingStrategy
from strategies.pricing_strategy import PricingStrategy


class SurgePricingStrategy(PricingStrategy):
    def __init__(
        self,
        base_strategy: BasicPricingStrategy | None = None,
        surge_multiplier: float = 1.5,
    ) -> None:
        self.base_strategy = base_strategy or BasicPricingStrategy()
        self.surge_multiplier = surge_multiplier

    def calculate_fare(self, pickup: Location, dropoff: Location) -> float:
        base_fare = self.base_strategy.calculate_fare(pickup, dropoff)
        return round(base_fare * self.surge_multiplier, 2)
