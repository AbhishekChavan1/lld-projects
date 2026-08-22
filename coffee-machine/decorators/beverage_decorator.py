from abc import abstractmethod

from models.beverage import Beverage


class BeverageDecorator(Beverage):
    """Base decorator: wraps any Beverage and delegates to it by default."""

    def __init__(self, beverage: Beverage):
        self._wrapped = beverage

    @abstractmethod
    def get_cost(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_recipe(self) -> dict[str, int]:
        raise NotImplementedError
