from dataclasses import dataclass, field

from models.locker import Locker


@dataclass
class LockerLocation:
    location_id: str
    name: str
    lockers: dict[str, Locker] = field(default_factory=dict)

    def add_locker(self, locker: Locker) -> None:
        self.lockers[locker.locker_id] = locker
