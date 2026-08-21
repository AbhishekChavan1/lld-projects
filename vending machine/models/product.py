import threading


class Product:
    def __init__(self, code: str, price: float, quantity: int):
        self.code = code
        self.price = price
        self._quantity = quantity
        self._lock = threading.Lock()

    def get_quantity(self) -> int:
        with self._lock:
            return self._quantity

    def decrement(self) -> None:
        with self._lock:
            self._quantity -= 1

    def restock(self, qty: int) -> None:
        with self._lock:
            self._quantity += qty
