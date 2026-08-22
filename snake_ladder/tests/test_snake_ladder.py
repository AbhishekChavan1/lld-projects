import pytest

from snake_ladder.models.board import Board
from snake_ladder.models.player import Player
from snake_ladder.services.game_manager import GameManager
from snake_ladder.strategies.dice_cup import DiceCup
from snake_ladder.strategies.loaded_die import LoadedDie
from snake_ladder.strategies.standard_die import StandardDie


class TestBoard:
    def test_add_snake_and_resolve(self):
        board = Board(100)
        board.add_snake(14, 4)
        assert board.resolve(14) == (4, 14)

    def test_add_ladder_and_resolve(self):
        board = Board(100)
        board.add_ladder(3, 38)
        assert board.resolve(3) == (38, 3)

    def test_normal_cell_unchanged(self):
        board = Board(100)
        assert board.resolve(50) == (50, None)

    def test_snake_head_must_be_above_tail(self):
        board = Board(100)
        with pytest.raises(ValueError):
            board.add_snake(4, 14)

    def test_ladder_base_must_be_below_top(self):
        board = Board(100)
        with pytest.raises(ValueError):
            board.add_ladder(38, 3)

    def test_endpoints_within_board(self):
        board = Board(100)
        with pytest.raises(ValueError):
            board.add_snake(105, 40)
        with pytest.raises(ValueError):
            board.add_snake(60, 0)
        with pytest.raises(ValueError):
            board.add_ladder(2, 101)

    def test_no_snake_on_winning_cell(self):
        board = Board(100)
        with pytest.raises(ValueError):
            board.add_snake(100, 10)

    def test_duplicate_source_rejected(self):
        board = Board(100)
        board.add_ladder(3, 38)
        with pytest.raises(ValueError):
            board.add_snake(3, 1)

    def test_chained_jumps_rejected(self):
        board = Board(100)
        board.add_snake(62, 19)
        with pytest.raises(ValueError):
            board.add_ladder(19, 45)
        board.add_ladder(9, 31)
        with pytest.raises(ValueError):
            board.add_snake(40, 9)

    def test_jumps_view_is_read_only(self):
        board = Board(100)
        board.add_snake(14, 4)
        with pytest.raises(TypeError):
            board.jumps[20] = 5


class TestPlayer:
    def test_starts_off_board(self):
        player = Player("Alice")
        assert player.position == 0

    def test_empty_name_rejected(self):
        with pytest.raises(ValueError):
            Player("   ")


class TestDice:
    def test_loaded_die_always_returns_value(self):
        die = LoadedDie(value=4)
        assert [die.roll() for _ in range(5)] == [4, 4, 4, 4, 4]

    def test_loaded_die_value_bounds(self):
        with pytest.raises(ValueError):
            LoadedDie(value=7)
        with pytest.raises(ValueError):
            LoadedDie(value=0)

    def test_standard_die_in_range(self):
        die = StandardDie(sides=6)
        rolls = {die.roll() for _ in range(200)}
        assert rolls.issubset({1, 2, 3, 4, 5, 6})
        assert len(rolls) > 1

    def test_standard_die_needs_two_sides(self):
        with pytest.raises(ValueError):
            StandardDie(sides=1)

    def test_dice_cup_sums_all_dice(self):
        cup = DiceCup([LoadedDie(3), LoadedDie(5)])
        assert cup.roll() == 8

    def test_dice_cup_requires_dice(self):
        with pytest.raises(ValueError):
            DiceCup([])


class TestGameManager:
    def _game(self, dice, size=10, snakes=(), ladders=()):
        board = Board(size)
        for head, tail in snakes:
            board.add_snake(head, tail)
        for base, top in ladders:
            board.add_ladder(base, top)
        return GameManager(board, dice, [Player("P1"), Player("P2")])

    def test_player_moves_forward(self, capsys):
        game = self._game(LoadedDie(3))
        game.take_turn()
        players = list(game._players)
        assert any(p.name == "P1" and p.position == 3 for p in players)

    def test_round_robin_order(self):
        game = self._game(LoadedDie(1))
        order = []
        for _ in range(6):
            current = game._players[0]
            order.append(current.name)
            game.take_turn()
        assert order == ["P1", "P2", "P1", "P2", "P1", "P2"]

    def test_overshoot_keeps_position(self):
        game = self._game(LoadedDie(4), size=10)
        p1 = game._players[0]
        p1.move_to(8)
        game.take_turn()
        assert p1.position == 8
        assert not game.is_game_over()

    def test_exact_landing_wins(self):
        game = self._game(LoadedDie(2), size=10)
        p1 = game._players[0]
        p1.move_to(8)
        game.take_turn()
        assert game.is_game_over()
        assert game.winner is p1

    def test_snake_slides_player_down(self):
        game = self._game(LoadedDie(2), size=10, snakes=[(9, 3)])
        p1 = game._players[0]
        p1.move_to(7)
        game.take_turn()
        assert not game.is_game_over()
        assert p1.position == 3

    def test_ladder_to_winning_cell_wins(self):
        game = self._game(LoadedDie(1), size=10, ladders=[(9, 10)])
        p1 = game._players[0]
        p1.move_to(8)
        game.take_turn()
        assert game.is_game_over()
        assert game.winner is p1

    def test_turns_after_win_are_noop(self):
        game = self._game(LoadedDie(2), size=10)
        p1 = game._players[0]
        p1.move_to(8)
        game.take_turn()
        game.take_turn()
        assert game.winner is p1

    def test_no_players_rejected(self):
        board = Board(10)
        with pytest.raises(ValueError):
            GameManager(board, LoadedDie(1), [])

    def test_full_simulation_with_single_die(self):
        game = self._game(LoadedDie(1), size=10)
        winner = game.play(max_turns=100)
        assert winner is not None
