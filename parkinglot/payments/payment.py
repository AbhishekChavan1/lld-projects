from abc import ABC, abstractmethod


class Payment(ABC):
    def __init__(self, amount: float):
        self.amount = amount

    @abstractmethod
    def process(self) -> bool:
        pass
