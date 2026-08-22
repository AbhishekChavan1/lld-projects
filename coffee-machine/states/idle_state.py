from .coffee_machine_state import CoffeeMachineState


class IdleState(CoffeeMachineState):
    def select_beverage(self, machine, beverage) -> None:
        from .payment_pending_state import PaymentPendingState

        machine.set_selected_beverage(beverage)
        machine.set_state(PaymentPendingState())
        print(f"Selected: {beverage.get_description()}. "
              f"Cost: ${beverage.get_cost():.2f}. Please pay.")

    def insert_coin(self, machine, amount) -> None:
        print("Select a beverage first before inserting coins.")

    def brew(self, machine) -> None:
        print("Select a beverage and insert coins first.")
