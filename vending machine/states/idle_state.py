from states.state import State


class IdleState(State):
    def insert_coin(self, machine, coin):
        machine.add_balance(coin.value)
        print(f"Inserted coin {coin.name}. Balance: ${machine.get_balance():.2f}")
        machine.set_state(machine.get_has_money_state())

    def select_product(self, machine, code):
        print("Insert coins first before choosing a product.")

    def dispense(self, machine):
        print("No coins loaded.")

    def cancel(self, machine):
        print("No transactional balance to cancel.")
