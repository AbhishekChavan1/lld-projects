from models.coin import Coin
from models.product import Product
from services.vending_machine import VendingMachine


def main():
    print("=== VENDING MACHINE STATE PATTERN DRIVER ===")
    machine = VendingMachine()

    machine.add_product(Product("Coke", 1.25, 2))
    machine.add_product(Product("Chips", 0.75, 1))

    print("\n--- Scenario 1: Buying Chips ($0.75) ---")
    machine.insert_coin(Coin.QUARTER)
    machine.insert_coin(Coin.DOLLAR)
    machine.select_product("Chips")

    print("\n--- Scenario 2: Insufficient Funds, then Cancel ---")
    machine.insert_coin(Coin.QUARTER)
    machine.insert_coin(Coin.DIME)
    machine.select_product("Coke")
    machine.cancel()

    print("\n--- Scenario 3: Successful Coke Purchase ---")
    machine.insert_coin(Coin.DOLLAR)
    machine.insert_coin(Coin.QUARTER)
    machine.select_product("Coke")

    print("\n--- Restocking admin simulation ---")
    coke = machine.get_product("Coke")
    print(f"Coke qty: {coke.get_quantity()}")
    coke.restock(5)
    print(f"Coke qty after restock: {coke.get_quantity()}")


if __name__ == "__main__":
    main()
