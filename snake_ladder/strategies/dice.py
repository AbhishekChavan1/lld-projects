from abc import ABC, abstractmethod


class DiceStrategy(ABC):
    @abstractmethod
    def roll(self) -> int:
        pass
