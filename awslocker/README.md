# AWS Locker

A Python locker assignment and pickup system — like Amazon Hub Locker logic, implemented as a clean, dependency-free library.

## Features

- **Size-aware assignment** — a package fits into the smallest matching locker (SMALL → small/medium/large, MEDIUM → medium/large, LARGE → large only)
- **Locker lifecycle** — lockers transition `AVAILABLE → OCCUPIED → AVAILABLE`
- **Package lifecycle** — packages transition `CREATED → READY_FOR_PICKUP → PICKED_UP`
- **Secure pickup codes** — random 6-digit codes generated with `secrets`
- **Typed exceptions** — no silent `False` returns; failures raise domain errors

## Project structure

```
awslocker/
├── main.py                  # CLI demo
├── models/                  # Domain entities & enums
│   ├── enums.py             # LockerSize, LockerStatus, PackageStatus
│   ├── locker.py            # Locker
│   ├── locker_location.py   # LockerLocation (holds lockers)
│   ├── package.py           # Package
│   └── user.py              # User
└── services/
    ├── exceptions.py        # Domain exceptions
    └── locker.py            # LockerService (assign / pickup logic)
```

## Requirements

- Python 3.10+ (uses `str | None` union syntax)
- No third-party dependencies

## Usage

```bash
python main.py
```

```python
from models.enums import LockerSize
from models.locker import Locker
from models.locker_location import LockerLocation
from models.package import Package
from services.locker import LockerService

location = LockerLocation(location_id="loc-1", name="Central Hub")
location.add_locker(Locker(locker_id="L1", size=LockerSize.SMALL))

service = LockerService()
package = Package(user_id="user-1", package_id="pkg-1", size=LockerSize.SMALL)

locker = service.assign_locker(location, package)  # -> Locker
service.pickup_package(location, "pkg-1", package.pickup_code)
```

## Exceptions

| Exception | Raised when |
|---|---|
| `LockerUnavailableError` | no locker of a fitting size is available |
| `PackageNotRegisteredError` | picking up a package unknown to the service |
| `InvalidPickupCodeError` | pickup code does not match |
| `PackageNotFoundError` | package is not in its expected locker |

All inherit from `LockerServiceError`.

## License

MIT
