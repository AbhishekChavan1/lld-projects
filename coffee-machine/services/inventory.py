import threading


class Inventory:
    """Thread-safe ingredient register guarded by an RLock."""

    def __init__(self, stock: dict[str, int] | None = None):
        self._lock = threading.RLock()
        self._stock: dict[str, int] = stock or {}

    def has_ingredients(self, recipe: dict[str, int]) -> bool:
        with self._lock:
            return all(self._stock.get(name, 0) >= qty for name, qty in recipe.items())

    def consume(self, recipe: dict[str, int]) -> None:
        with self._lock:
            for name, qty in recipe.items():
                if self._stock.get(name, 0) < qty:
                    raise ValueError(f"Insufficient {name} in inventory.")
                self._stock[name] -= qty

    def restock(self, recipe: dict[str, int]) -> None:
        with self._lock:
            for name, qty in recipe.items():
                self._stock[name] = self._stock.get(name, 0) + qty

    def get_stock(self) -> dict[str, int]:
        with self._lock:
            return dict(self._stock)
