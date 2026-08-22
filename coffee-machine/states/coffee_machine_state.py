from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.beverage import Beverage
    from machine.coffee_machine import CoffeeMachine


class CoffeeMachineState(ABC):
    """Interface for machine lifecycle states (State Pattern)."""

    @abstractmethod
    def select_beverage(self, machine: "CoffeeMachine", beverage: "Beverage") -> None:
        raise NotImplementedError

    @abstractmethod
    def insert_coin(self, machine: "CoffeeMachine", amount: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def brew(self, machine: "CoffeeMachine") -> None:
        raise NotImplementedError
