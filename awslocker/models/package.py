from dataclasses import dataclass

from models.enums import LockerSize, PackageStatus


@dataclass
class Package:
    user_id: str
    package_id: str
    size: LockerSize
    locker_id: str | None = None
    pickup_code: str | None = None
    status: PackageStatus = PackageStatus.CREATED
