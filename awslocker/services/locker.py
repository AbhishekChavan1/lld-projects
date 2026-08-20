import secrets

from models.enums import LockerSize, LockerStatus, PackageStatus
from models.locker import Locker
from models.locker_location import LockerLocation
from models.package import Package
from services.exceptions import (
    InvalidPickupCodeError,
    LockerServiceError,
    LockerUnavailableError,
    PackageNotRegisteredError,
    PackageNotFoundError,
)


class LockerService:
    def __init__(self) -> None:
        self.packages: dict[str, Package] = {}

    def register_package(self, package: Package) -> None:
        self.packages[package.package_id] = package

    def get_package(self, package_id: str) -> Package | None:
        return self.packages.get(package_id)

    def find_locker(
        self, location: LockerLocation, package_size: LockerSize
    ) -> Locker | None:
        size_priority = {
            LockerSize.SMALL: [LockerSize.SMALL, LockerSize.MEDIUM, LockerSize.LARGE],
            LockerSize.MEDIUM: [LockerSize.MEDIUM, LockerSize.LARGE],
            LockerSize.LARGE: [LockerSize.LARGE],
        }

        for size in size_priority[package_size]:
            for locker in location.lockers.values():
                if locker.size == size and locker.status == LockerStatus.AVAILABLE:
                    return locker

        return None

    def generate_pickup_code(self, length: int = 6) -> str:
        return f"{secrets.randbelow(10 ** length):0{length}d}"

    def assign_locker(
        self,
        location: LockerLocation,
        package: Package,
        package_size: LockerSize | None = None,
    ) -> Locker:
        locker = self.find_locker(location, package_size or package.size)

        if locker is None:
            raise LockerUnavailableError(
                f"no available locker for package {package.package_id}"
            )

        self.register_package(package)

        locker.status = LockerStatus.OCCUPIED
        locker.package_id = package.package_id

        package.locker_id = locker.locker_id
        package.pickup_code = self.generate_pickup_code()
        package.status = PackageStatus.READY_FOR_PICKUP

        return locker

    def pickup_package(
        self, location: LockerLocation, package_id: str, pickup_code: str
    ) -> None:
        package = self.get_package(package_id)

        if package is None:
            raise PackageNotRegisteredError(f"package {package_id} is not registered")

        if package.pickup_code != pickup_code:
            raise InvalidPickupCodeError(f"invalid pickup code for package {package_id}")

        if package.locker_id is None:
            raise LockerServiceError(
                f"package {package_id} has no assigned locker"
            )

        locker = location.lockers.get(package.locker_id)

        if locker is None or locker.package_id != package.package_id:
            raise PackageNotFoundError(
                f"package {package_id} not found in locker {package.locker_id}"
            )

        locker.status = LockerStatus.AVAILABLE
        locker.package_id = None

        package.status = PackageStatus.PICKED_UP
        package.locker_id = None
