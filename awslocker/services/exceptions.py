class LockerServiceError(Exception):
    pass


class PackageNotRegisteredError(LockerServiceError):
    pass


class LockerUnavailableError(LockerServiceError):
    pass


class PackageNotFoundError(LockerServiceError):
    pass


class InvalidPickupCodeError(LockerServiceError):
    pass
