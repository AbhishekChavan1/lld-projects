from dataclasses import dataclass

from models.enums import LockerSize, LockerStatus


@dataclass
class Locker:
    locker_id: str
    size: LockerSize
    status: LockerStatus = LockerStatus.AVAILABLE
    package_id: str | None = None