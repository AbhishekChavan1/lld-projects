from states.state import State


class OutOfStockState(State):
    def insert_coin(self, machine, coin):
        print("Machine is completely Out of Stock.")

    def select_product(self, machine, code):
        print("Machine is completely Out of Stock.")

    def dispense(self, machine):
        print("Nothing to dispense.")

    def cancel(self, machine):
        print("Nothing to cancel.")
