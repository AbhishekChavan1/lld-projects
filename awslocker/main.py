from models.enums import LockerSize
from models.locker import Locker
from models.locker_location import LockerLocation
from models.package import Package
from services.exceptions import InvalidPickupCodeError
from services.locker import LockerService


def main() -> None:
    location = LockerLocation(location_id="loc-1", name="Central Hub")
    location.add_locker(Locker(locker_id="L1", size=LockerSize.SMALL))
    location.add_locker(Locker(locker_id="L2", size=LockerSize.MEDIUM))

    service = LockerService()
    package = Package(user_id="user-1", package_id="pkg-1", size=LockerSize.SMALL)

    locker = service.assign_locker(location, package)

    print(f"assigned locker={locker.locker_id}")
    print(f"package_status={package.status.value}")
    print(f"pickup_code={package.pickup_code}")

    try:
        service.pickup_package(location, "pkg-1", "000000")
    except InvalidPickupCodeError as exc:
        print(f"wrong code rejected: {exc}")

    service.pickup_package(location, "pkg-1", package.pickup_code)
    print(f"package_status={package.status.value}")


if __name__ == "__main__":
    main()
