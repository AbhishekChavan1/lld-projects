from states.state import State


class DispensingState(State):
    def insert_coin(self, machine, coin):
        print("Currently dispensing, please wait.")

    def select_product(self, machine, code):
        print("Currently dispensing, please wait.")

    def dispense(self, machine):
        product = machine.get_product(machine.get_selected_product())
        product.decrement()
        change = machine.round2(machine.get_balance() - product.price)
        print(f"Dispensing product {product.code} (${product.price:.2f})")
        if change > 0:
            print(f"Change due: ${change:.2f}")
            if not machine.return_change(change):
                print("Refunding complete amount...")
                machine.return_change(machine.get_balance())
                product.restock(1)
        machine.clear_balance()
        machine.set_selected_product(None)

        all_out = all(
            p.get_quantity() <= 0 for p in machine.get_all_products()
        )
        machine.set_state(
            machine.get_out_of_stock_state() if all_out else machine.get_idle_state()
        )

    def cancel(self, machine):
        print("Cannot cancel while dispensing is in progress.")
