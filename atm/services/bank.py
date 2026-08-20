class Bank:
    def __init__(self):
        self.cards = {}

    def add_card(self, card):
        self.cards[card.number] = card

    def get_card(self, card_number):
        return self.cards.get(card_number, None)