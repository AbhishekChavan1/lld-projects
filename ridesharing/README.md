# Ridesharing

A strategy-driven ridesharing system built with clean architecture. It matches riders with drivers using pluggable matching strategies, prices rides with pluggable pricing strategies, and settles payments via a wallet-based payment service.

## Features

- **Models**: `User`, `Driver`, `Rider`, `Location`, `Ride`, `RideRequest`, `Payment`, `Vehicle` and status enums (`RideStatus`, `PaymentStatus`, `VehicleType`).
- **Matching strategies**: nearest driver, cheapest driver, highest rated driver.
- **Pricing strategies**: basic (per-km) and surge pricing.
- **Payment service**: wallet-based, produces `Payment` records with `PENDING` / `COMPLETED` / `FAILED` statuses.
- **Ride lifecycle**: `REQUESTED` -> `DRIVER_ASSIGNED` -> `DRIVING` -> `COMPLETED` (or `CANCELLED`).

## Project structure

```
ridesharing/
├── enums/                 # RideStatus, PaymentStatus, VehicleType
├── models/                # Domain entities (Driver, Rider, Ride, Location, ...)
├── services/              # RideService, MatchingService, PaymentService
├── strategies/            # Matching & pricing strategy interfaces and implementations
├── tests/                 # pytest test suite
└── main.py                # Demo of a full ride lifecycle
```

## Quick start

```bash
python main.py
```

Expected output:

```
Ride RIDE-0001 created
  Driver : John Driver (ABC123)
  Fare   : $32.36
  Status : driver_assigned
Ride RIDE-0001 started - status: driving
Ride RIDE-0001 completed - status: completed
Payment PAY-0001: Completed ($32.36)
Rider balance: $467.64
Driver available again: True
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

## Usage example

```python
from models.driver import Driver
from models.rider import Rider
from models.location import Location
from models.vehicle import Vehicle
from enums.vehicletype import VehicleType
from services.matching import MatchingService
from services.paymentservices import PaymentService
from services.rideservices import RideService
from strategies.basic_pricing_strategy import BasicPricingStrategy
from strategies.nearest_driver_strategy import NearestDriverStrategy

service = RideService(
    matching_service=MatchingService(NearestDriverStrategy()),
    pricing_strategy=BasicPricingStrategy(rate_per_km=10.0),
    payment_service=PaymentService(),
)

driver = Driver("D001", "John", "john@driver.com", "1234567890", "DL-1001")
driver.set_vehicle(Vehicle("V001", VehicleType.CAR, "ABC123"))
driver.set_location(Location("Midtown NYC", 40.7549, -73.9840))
service.add_driver(driver)

rider = Rider("P001", "Alice", "alice@pass.com", "1122334455")
service.add_wallet_balance(rider, 100.0)

ride = service.request_ride(
    rider,
    Location("Times Square", 40.7580, -73.9855),
    Location("Central Park", 40.7812, -73.9665),
)
service.start_ride(ride.ride_id)
payment = service.complete_ride(ride.ride_id)
print(payment.status)  # PaymentStatus.COMPLETED
```

## Extending

Implement the abstract strategy interfaces and inject them into `RideService`:

- `MatchingStrategy.match(ride_request, drivers)` - pick a driver
- `PricingStrategy.calculate_fare(pickup, dropoff)` - compute the fare
