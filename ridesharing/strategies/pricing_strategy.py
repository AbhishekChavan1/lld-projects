from abc import ABC, abstractmethod

from models.location import Location


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_fare(self, pickup: Location, dropoff: Location) -> float:
        """Calculate the fare for a ride between two locations."""
        pass
