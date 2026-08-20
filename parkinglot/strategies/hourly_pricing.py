from datetime import datetime

from .pricing import PricingStrategy


class HourlyRatePricing(PricingStrategy):
    def __init__(self, hourly_rate: float):
        self.hourly_rate = hourly_rate

    def calculate_price(self, entry_time: datetime, exit_time: datetime) -> float:
        duration = exit_time - entry_time
        hours = max(duration.total_seconds() / 3600, 1.0)
        return round(self.hourly_rate * hours, 2)
