from abc import ABC, abstractmethod
from datetime import datetime


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, entry_time: datetime, exit_time: datetime) -> float:
        pass
