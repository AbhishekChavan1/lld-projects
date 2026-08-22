from .coffee_machine_state import CoffeeMachineState


class PaymentPendingState(CoffeeMachineState):
    def select_beverage(self, machine, beverage) -> None:
        print("Payment already pending. Complete it or cancel.")

    def insert_coin(self, machine, amount) -> None:
        from .brewing_state import BrewingState

        machine.add_inserted_cash(amount)
        cost = machine.get_selected_beverage().get_cost()
        total = machine.get_inserted_cash()
        print(f"Paid: ${amount:.2f}. Total inserted: ${total:.2f}. Required: ${cost:.2f}")
        if total >= cost:
            machine.set_state(BrewingState())
            print("Payment complete. Ready to brew.")

    def brew(self, machine) -> None:
        print("Payment incomplete.")
