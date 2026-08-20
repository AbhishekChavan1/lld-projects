from enum import Enum

class LockerSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class LockerStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    OUT_OF_SERVICE = "out_of_service"

class PackageStatus(Enum):
    CREATED = "created"
    ASSIGNED = "assigned"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    EXPIRED = "expired"
