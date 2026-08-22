# Snake & Ladder

A Python implementation of the classic Snake & Ladder game demonstrating **Strategy Pattern**, **SRP**, and an immutable-rule / mutable-state separation.

## Features

- Dynamic board size (default 100) with configurable snakes and ladders
- Round-robin turn management for N players via a queue
- Pluggable dice: any number of dice (M), each with configurable sides (S)
- Strict win condition - exact landing on the last cell; overshoots are rejected
- Board validation: no invalid/chained/overlapping jumps, no snake on the winning cell

## Design Patterns

- **Strategy Pattern** - `DiceStrategy` abstraction lets you swap `StandardDie`, `DiceCup` (M dice summed), or a rigged `LoadedDie` for deterministic tests
- **Single Responsibility Principle** - `Board` owns structural pathways only, `DiceStrategy` implementations only generate values, `GameManager` only runs the turn loop
- **Immutability of rules** - the board's jump table is frozen after setup and exposed as a read-only mapping; player state mutates independently

## Structure

```
snake_ladder/
├── models/
│   ├── player.py              # Player with current position
│   └── board.py               # Board + validated snake/ladder jump table
├── strategies/
│   ├── dice.py                # DiceStrategy ABC
│   ├── standard_die.py        # Fair die with configurable sides
│   ├── loaded_die.py          # Rigged die (deterministic testing)
│   └── dice_cup.py            # Composite rolling M dice at once
├── services/
│   └── game_manager.py        # Turn loop, overshoot rule, win check
├── tests/
│   └── test_snake_ladder.py   # 27 pytest tests
├── main.py                    # Demo entry point
└── README.md
```

## Quick Start

```bash
python -m snake_ladder.main
```

## Running Tests

```bash
python -m pytest snake_ladder/tests/ -v
```
