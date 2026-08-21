import threading

from models.coin import Coin
from models.product import Product
from states.dispensing_state import DispensingState
from states.has_money_state import HasMoneyState
from states.idle_state import IdleState
from states.out_of_stock_state import OutOfStockState


class VendingMachine:
    def __init__(self):
        self._inventory = {}
        self._coin_inventory = {
            Coin.NICKEL: 20,
            Coin.DIME: 10,
            Coin.QUARTER: 10,
            Coin.DOLLAR: 5,
        }
        self._current_balance = 0.0
        self._selected_product_code = None
        self._lock = threading.Lock()

        self._idle_state = IdleState()
        self._has_money_state = HasMoneyState()
        self._dispensing_state = DispensingState()
        self._out_of_stock_state = OutOfStockState()
        self._current_state = self._idle_state

    def add_product(self, product: Product) -> None:
        self._inventory[product.code] = product

    def get_product(self, code: str):
        return self._inventory.get(code)

    def get_all_products(self):
        return list(self._inventory.values())

    def set_state(self, state) -> None:
        self._current_state = state

    def get_idle_state(self):
        return self._idle_state

    def get_has_money_state(self):
        return self._has_money_state

    def get_dispensing_state(self):
        return self._dispensing_state

    def get_out_of_stock_state(self):
        return self._out_of_stock_state

    def get_balance(self) -> float:
        return self._current_balance

    def add_balance(self, amount: float) -> None:
        self._current_balance = self.round2(self._current_balance + amount)

    def clear_balance(self) -> None:
        self._current_balance = 0.0

    def set_selected_product(self, code) -> None:
        self._selected_product_code = code

    def get_selected_product(self):
        return self._selected_product_code

    def round2(self, amount: float) -> float:
        return round(amount + 1e-9, 2)

    def insert_coin(self, coin: Coin) -> None:
        with self._lock:
            self._current_state.insert_coin(self, coin)

    def select_product(self, code: str) -> None:
        with self._lock:
            self._current_state.select_product(self, code)

    def dispense_internal(self) -> None:
        self._current_state.dispense(self)

    def dispense(self) -> None:
        with self._lock:
            self.dispense_internal()

    def cancel(self) -> None:
        with self._lock:
            self._current_state.cancel(self)

    def add_coins(self, coin: Coin, count: int) -> None:
        self._coin_inventory[coin] = self._coin_inventory.get(coin, 0) + count

    def return_change(self, change_amount: float) -> bool:
        remaining = self.round2(change_amount)
        if remaining == 0.0:
            return True

        dispensed = {}
        for coin in (Coin.DOLLAR, Coin.QUARTER, Coin.DIME, Coin.NICKEL):
            needed = int(remaining / coin.value)
            if needed > 0:
                available = self._coin_inventory.get(coin, 0)
                take = min(needed, available)
                if take > 0:
                    dispensed[coin] = take
                    remaining = self.round2(remaining - take * coin.value)

        if remaining > 0.0:
            print("System Alert: Insufficient physical coins to return change!")
            return False

        for coin, count in dispensed.items():
            self._coin_inventory[coin] -= count
            print(f"Returned change coin: {coin.name} x{count}")
        return True
