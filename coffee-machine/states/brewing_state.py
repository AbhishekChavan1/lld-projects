from .coffee_machine_state import CoffeeMachineState


class BrewingState(CoffeeMachineState):
    def select_beverage(self, machine, beverage) -> None:
        print("Cannot change beverage while brewing.")

    def insert_coin(self, machine, amount) -> None:
        print("Cannot insert coins while brewing.")

    def brew(self, machine) -> None:
        beverage = machine.get_selected_beverage()
        if not machine.inventory.has_ingredients(beverage.get_recipe()):
            print(f"Insufficient ingredients for {beverage.get_description()}! Refunding cash...")
            refund = machine.get_inserted_cash()
            if refund > 0:
                print(f"Refunded: ${refund:.2f}")
            machine.reset_cash()
            machine.set_selected_beverage(None)
            machine.set_state(IdleState())
            return

        print(f"Brewing {beverage.get_description()}...")
        machine.inventory.consume(beverage.get_recipe())

        change = round(machine.get_inserted_cash() - beverage.get_cost(), 2)
        if change > 0:
            print(f"Dispensing change: ${change:.2f}")

        machine.reset_cash()
        machine.set_selected_beverage(None)
        machine.set_state(IdleState())
        print("Enjoy your premium coffee!")


from .idle_state import IdleState  # noqa: E402
