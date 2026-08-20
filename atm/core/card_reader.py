class CardReader:
    def __init__(self):
        self.card = None

    def insert_card(self, card):
        self.card = card
        return self.card

    def eject_card(self):
        self.card = None
        return self.card