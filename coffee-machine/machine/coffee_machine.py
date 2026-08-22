import threading

from services.inventory import Inventory
from states.coffee_machine_state import CoffeeMachineState
from states.idle_state import IdleState


class CoffeeMachine:
    """Context object: proxies public calls to the current State."""

    def __init__(self, inventory: Inventory | None = None):
        self._lock = threading.RLock()
        self.inventory = inventory or Inventory({
            "coffee_beans": 10,
            "water": 20,
            "milk": 5,
            "sugar": 5,
            "caramel_syrup": 3,
        })
        self._state: CoffeeMachineState = IdleState()
        self._selected_beverage = None
        self._inserted_cash = 0.0

    # ── accessors used by states ─────────────────────────────────────────
    def set_state(self, state: CoffeeMachineState) -> None:
        with self._lock:
            self._state = state

    def get_state(self) -> CoffeeMachineState:
        return self._state

    def set_selected_beverage(self, beverage) -> None:
        self._selected_beverage = beverage

    def get_selected_beverage(self):
        return self._selected_beverage

    def add_inserted_cash(self, amount: float) -> None:
        self._inserted_cash += amount

    def get_inserted_cash(self) -> float:
        return self._inserted_cash

    def reset_cash(self) -> None:
        self._inserted_cash = 0.0

    # ── public API (proxy state triggers) ────────────────────────────────
    def select_beverage(self, beverage) -> None:
        with self._lock:
            self._state.select_beverage(self, beverage)

    def insert_coin(self, amount: float) -> None:
        with self._lock:
            self._state.insert_coin(self, amount)

    def brew(self) -> None:
        with self._lock:
            self._state.brew(self)
