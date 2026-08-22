from snake_ladder.models.board import Board
from snake_ladder.models.player import Player
from snake_ladder.services.game_manager import GameManager
from snake_ladder.strategies.dice_cup import DiceCup
from snake_ladder.strategies.standard_die import StandardDie


def build_board() -> Board:
    board = Board(size=100)

    snakes = [(14, 4), (37, 17), (62, 19), (96, 56)]
    ladders = [(3, 38), (9, 31), (40, 59), (75, 95)]
    for head, tail in snakes:
        board.add_snake(head, tail)
    for base, top in ladders:
        board.add_ladder(base, top)
    return board


def main():
    board = build_board()

    dice_cup = DiceCup([StandardDie(sides=6)])
    players = [Player("Alice"), Player("Bob"), Player("Charlie")]

    game = GameManager(board, dice_cup, players)

    print("--- Snake & Ladder ---")
    winner = game.play(max_turns=500)
    if winner is None:
        print("--- No winner within turn cap. ---")


if __name__ == "__main__":
    main()
