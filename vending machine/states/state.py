from abc import ABC, abstractmethod


class State(ABC):
    @abstractmethod
    def insert_coin(self, machine, coin):
        pass

    @abstractmethod
    def select_product(self, machine, code):
        pass

    @abstractmethod
    def dispense(self, machine):
        pass

    @abstractmethod
    def cancel(self, machine):
        pass
