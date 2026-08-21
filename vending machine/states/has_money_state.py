from states.state import State


class HasMoneyState(State):
    def insert_coin(self, machine, coin):
        machine.add_balance(coin.value)
        print(f"Inserted another coin {coin.name}. Balance: ${machine.get_balance():.2f}")

    def select_product(self, machine, code):
        product = machine.get_product(code)
        if product is None or product.get_quantity() <= 0:
            print(f"Product {code} is out of stock.")
            return
        if machine.get_balance() < product.price:
            print(
                f"Insufficient funds! Needs ${product.price:.2f}, "
                f"current: ${machine.get_balance():.2f}"
            )
            return
        machine.set_selected_product(code)
        machine.set_state(machine.get_dispensing_state())
        print(f"Product {product.code} selected. Transitioning to dispensing.")
        machine.dispense_internal()

    def dispense(self, machine):
        print("Select a product to initiate dispense.")

    def cancel(self, machine):
        change = machine.get_balance()
        print(f"Transaction cancelled. Returning change: ${change:.2f}")
        machine.return_change(change)
        machine.clear_balance()
        machine.set_state(machine.get_idle_state())
