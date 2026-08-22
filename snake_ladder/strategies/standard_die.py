import random

from snake_ladder.strategies.dice import DiceStrategy


class StandardDie(DiceStrategy):
    def __init__(self, sides: int = 6):
        if sides < 2:
            raise ValueError("A die needs at least 2 sides.")
        self.sides = sides
        self._random = random.Random()

    def roll(self) -> int:
        return self._random.randint(1, self.sides)
