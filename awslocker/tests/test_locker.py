import pytest

from awslocker.models.enums import LockerSize, LockerStatus, PackageStatus
from awslocker.models.locker import Locker
from awslocker.models.locker_location import LockerLocation
from awslocker.models.package import Package
from awslocker.services.exceptions import (
    InvalidPickupCodeError,
    LockerUnavailableError,
    PackageNotRegisteredError,
)
from awslocker.services.locker import LockerService


@pytest.fixture
def service():
    return LockerService()


@pytest.fixture
def location():
    loc = LockerLocation(location_id="LOC1", name="Downtown Hub")
    loc.add_locker(Locker(locker_id="L1", size=LockerSize.SMALL))
    loc.add_locker(Locker(locker_id="L2", size=LockerSize.MEDIUM))
    loc.add_locker(Locker(locker_id="L3", size=LockerSize.LARGE))
    return loc


@pytest.fixture
def small_package():
    return Package(user_id="user1", package_id="PKG001", size=LockerSize.SMALL)


def test_assign_locker_small_package(service, location, small_package):
    locker = service.assign_locker(location, small_package)
    assert locker.locker_id == "L1"
    assert locker.status == LockerStatus.OCCUPIED
    assert small_package.status == PackageStatus.READY_FOR_PICKUP
    assert small_package.pickup_code is not None
    assert small_package.locker_id == "L1"


def test_assign_locker_uses_next_available_size(service, location):
    pkg = Package(user_id="user1", package_id="PKG002", size=LockerSize.SMALL)
    service.assign_locker(location, pkg)
    assert pkg.locker_id == "L1"

    pkg2 = Package(user_id="user1", package_id="PKG003", size=LockerSize.SMALL)
    service.assign_locker(location, pkg2)
    assert pkg2.locker_id == "L2"

    pkg3 = Package(user_id="user1", package_id="PKG004", size=LockerSize.SMALL)
    service.assign_locker(location, pkg3)
    assert pkg3.locker_id == "L3"


def test_assign_locker_no_available(service, location):
    for i in range(3):
        pkg = Package(user_id="user1", package_id=f"PKG{i}", size=LockerSize.SMALL)
        service.assign_locker(location, pkg)

    full_pkg = Package(user_id="user1", package_id="PKG_FULL", size=LockerSize.SMALL)
    with pytest.raises(LockerUnavailableError):
        service.assign_locker(location, full_pkg)


def test_pickup_package(service, location, small_package):
    service.assign_locker(location, small_package)
    code = small_package.pickup_code

    service.pickup_package(location, small_package.package_id, code)
    assert small_package.status == PackageStatus.PICKED_UP
    assert small_package.locker_id is None

    locker = location.lockers["L1"]
    assert locker.status == LockerStatus.AVAILABLE
    assert locker.package_id is None


def test_pickup_wrong_code(service, location, small_package):
    service.assign_locker(location, small_package)
    with pytest.raises(InvalidPickupCodeError):
        service.pickup_package(location, small_package.package_id, "000000")


def test_pickup_unregistered(service, location):
    with pytest.raises(PackageNotRegisteredError):
        service.pickup_package(location, "NONEXISTENT", "000000")


def test_package_lookup(service, small_package):
    service.register_package(small_package)
    assert service.get_package(small_package.package_id) == small_package
    assert service.get_package("NONEXISTENT") is None


def test_pickup_code_format(service):
    code = service.generate_pickup_code(6)
    assert len(code) == 6
    assert code.isdigit()
