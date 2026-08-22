from types import MappingProxyType


class Board:
    def __init__(self, size: int = 100):
        if size < 2:
            raise ValueError("Board size must be at least 2.")
        self.size = size
        self._jumps: dict[int, int] = {}

    @property
    def jumps(self):
        return MappingProxyType(self._jumps)

    def add_snake(self, head: int, tail: int) -> None:
        if not (1 <= tail < head <= self.size):
            raise ValueError(
                f"Invalid snake {head}->{tail}: need 1 <= tail < head <= {self.size}."
            )
        if head == self.size:
            raise ValueError("A snake head cannot sit on the winning cell.")
        self._set_jump(head, tail)

    def add_ladder(self, base: int, top: int) -> None:
        if not (1 <= base < top <= self.size):
            raise ValueError(
                f"Invalid ladder {base}->{top}: need 1 <= base < top <= {self.size}."
            )
        self._set_jump(base, top)

    def _set_jump(self, src: int, dst: int) -> None:
        if src in self._jumps:
            raise ValueError(f"Cell {src} already hosts a jump.")
        if dst in self._jumps:
            raise ValueError(
                f"Cell {dst} is the base/head of another jump; chained jumps are not allowed."
            )
        if any(existing_dst == src for existing_dst in self._jumps.values()):
            raise ValueError(
                f"Cell {src} is the tail/top of another jump; chained jumps are not allowed."
            )
        self._jumps[src] = dst

    def resolve(self, position: int) -> tuple[int, int | None]:
        dst = self._jumps.get(position)
        return (dst, position) if dst is not None else (position, None)
