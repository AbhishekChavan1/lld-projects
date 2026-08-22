from decorators.caramel_syrup_decorator import CaramelSyrupDecorator
from decorators.milk_decorator import MilkDecorator
from decorators.sugar_decorator import SugarDecorator
from machine.coffee_machine import CoffeeMachine
from models.americano import Americano
from models.espresso import Espresso


def main() -> None:
    print("=== Advanced Coffee Machine ===")
    machine = CoffeeMachine()

    print("\n--- Order 1: Custom Espresso (Milk + Sugar) ---")
    double_sweet_espresso = SugarDecorator(MilkDecorator(Espresso()))
    machine.select_beverage(double_sweet_espresso)
    machine.insert_coin(1.00)
    machine.insert_coin(2.00)  # Exceeds target cost of 2.70
    machine.brew()

    print("\n--- Order 2: Americano with Caramel Syrup ---")
    caramel_americano = CaramelSyrupDecorator(Americano())
    machine.select_beverage(caramel_americano)
    machine.insert_coin(3.10)
    machine.brew()

    print("\n--- Order 3: Invalid flow (coin before selection) ---")
    machine.insert_coin(1.00)
    machine.brew()

    print("\n--- Order 4: Insufficient ingredients -> refund ---")
    machine.inventory.restock({"coffee_beans": -10})  # simulate empty beans
    machine.select_beverage(MilkDecorator(Espresso()))
    machine.insert_coin(2.50)
    machine.brew()
    machine.inventory.restock({"coffee_beans": 10})   # restock for next run

    print(f"\nFinal inventory: {machine.inventory.get_stock()}")


if __name__ == "__main__":
    main()
