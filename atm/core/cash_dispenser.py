class CashDispenser:
    def __init__(self):
        self.notes = {
            500:100,
            200:100,
            100:100,
            50:100,
        }

    def get_total_cash(self):
        total_cash = 0
        for denomination, count in self.notes.items():
            total_cash += denomination * count
        return total_cash

    def dispense_cash(self, amount):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.get_total_cash():
            raise ValueError("Insufficient funds in ATM")
        remaining = amount
        plan = {}
        for denomination in sorted(self.notes.keys(), reverse=True):
            if remaining >= denomination:
                num_notes = min(remaining // denomination, self.notes[denomination])
                if num_notes > 0:
                    plan[denomination] = num_notes
                    remaining -= denomination * num_notes
        if remaining > 0:
            raise ValueError("Cannot dispense the requested amount with available denominations")
        for denomination, count in plan.items():
            self.notes[denomination] -= count
        return plan