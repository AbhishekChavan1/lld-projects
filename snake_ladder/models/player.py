class Player:
    def __init__(self, name: str):
        if not name or not name.strip():
            raise ValueError("Player name cannot be empty.")
        self.name = name.strip()
        self.position = 0

    def move_to(self, position: int) -> None:
        self.position = position

    def __repr__(self) -> str:
        return f"Player({self.name!r}, position={self.position})"
