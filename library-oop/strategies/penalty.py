from abc import ABC, abstractmethod


class Penalty(ABC):
    @abstractmethod
    def calculate_fine(self, days_overdue: int) -> float:
        pass
