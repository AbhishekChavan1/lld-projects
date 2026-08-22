from abc import ABC, abstractmethod


class Beverage(ABC):
    """Common interface for base coffees and condiment decorators alike."""

    @abstractmethod
    def get_cost(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_recipe(self) -> dict[str, int]:
        """Ingredients consumed to prepare this beverage."""
        raise NotImplementedError

    def __str__(self) -> str:
        return f"{self.get_description()} (${self.get_cost():.2f})"
