from snake_ladder.strategies.dice import DiceStrategy


class LoadedDie(DiceStrategy):
    def __init__(self, value: int, sides: int = 6):
        if not (1 <= value <= sides):
            raise ValueError(f"LoadedDie value must be within 1..{sides}.")
        self.value = value
        self.sides = sides

    def roll(self) -> int:
        return self.value
