from datetime import datetime

from .pricing import PricingStrategy


class FlatRatePricing(PricingStrategy):
    def __init__(self, flat_rate: float):
        self.flat_rate = flat_rate

    def calculate_price(self, entry_time: datetime, exit_time: datetime) -> float:
        return self.flat_rate
