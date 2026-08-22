from collections import deque

from snake_ladder.models.board import Board
from snake_ladder.models.player import Player
from snake_ladder.strategies.dice import DiceStrategy


class GameManager:
    def __init__(self, board: Board, dice: DiceStrategy, players: list[Player]):
        if not players:
            raise ValueError("A game needs at least one player.")
        self._board = board
        self._dice = dice
        self._players = deque(players)
        self._winner: Player | None = None

    @property
    def winner(self) -> Player | None:
        return self._winner

    def is_game_over(self) -> bool:
        return self._winner is not None

    def take_turn(self) -> None:
        if self.is_game_over():
            return

        current = self._players.popleft()
        roll = self._dice.roll()
        print(f"[Game] {current.name} rolled {roll} (at cell {current.position})")

        next_pos = current.position + roll
        if next_pos > self._board.size:
            print(
                f"[Game] {current.name} overshoots ({next_pos} > {self._board.size}); "
                "needs an exact landing - staying put."
            )
            next_pos = current.position
        else:
            next_pos, jump = self._board.resolve(next_pos)
            if jump is not None and next_pos < jump:
                print(f"[Board] {current.name} hits a snake at {jump} -> slides down to {next_pos}")
            elif jump is not None:
                print(f"[Board] {current.name} hits a ladder at {jump} -> climbs up to {next_pos}")

        current.move_to(next_pos)
        print(f"[Game] {current.name} now stands on cell {next_pos}")

        if next_pos == self._board.size:
            self._winner = current
            print(f"[Victory] {current.name} wins the game!")
            return

        self._players.append(current)

    def play(self, max_turns: int = 1000) -> Player | None:
        turns = 0
        while not self.is_game_over() and turns < max_turns:
            self.take_turn()
            turns += 1
        if self._winner is None:
            print(f"[Game] Turn cap of {max_turns} reached; game ended without a winner.")
        else:
            print(f"[Game] Game finished after {turns} turns.")
        return self._winner
