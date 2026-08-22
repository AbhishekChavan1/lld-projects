from snake_ladder.strategies.dice import DiceStrategy


class DiceCup(DiceStrategy):
    def __init__(self, dice: list[DiceStrategy]):
        if not dice:
            raise ValueError("A dice cup needs at least one die.")
        self.dice = list(dice)

    def roll(self) -> int:
        return sum(die.roll() for die in self.dice)
