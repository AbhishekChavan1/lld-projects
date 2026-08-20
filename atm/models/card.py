class Card:
    def __init__(self, name, number, pin, account):
        self.name = name
        self.number = number
        self.pin = pin
        self.account = account
        self.is_blocked = False
        self.failed_attempts = 0

    def register_failed_attempt(self):
        self.failed_attempts += 1
        return self.failed_attempts

    def reset_failed_attempts(self):
        self.failed_attempts = 0

    def validate_pin(self, input_pin):
        return self.pin == input_pin

    def change_pin(self, old_pin, new_pin):
        if self.validate_pin(old_pin):
            self.pin = new_pin
            return True
        return False

    def block(self):
        self.is_blocked = True

    def unblock(self):
        self.is_blocked = False
