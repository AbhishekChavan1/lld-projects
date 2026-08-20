from enums.vehicletype import VehicleType
from models.driver import Driver
from models.location import Location
from models.rider import Rider
from models.vehicle import Vehicle
from services.matching import MatchingService
from services.paymentservices import PaymentService
from services.rideservices import RideService
from strategies.basic_pricing_strategy import BasicPricingStrategy
from strategies.nearest_driver_strategy import NearestDriverStrategy


def main() -> None:
    service = RideService(
        matching_service=MatchingService(NearestDriverStrategy()),
        pricing_strategy=BasicPricingStrategy(rate_per_km=10.0),
        payment_service=PaymentService(),
    )

    # Register drivers and their vehicles
    john = Driver("D001", "John Driver", "john@driver.com", "1234567890", "DL-1001")
    john.set_vehicle(Vehicle("V001", VehicleType.CAR, "ABC123"))
    john.set_location(Location("Midtown NYC", 40.7549, -73.9840))
    john.update_rating(4.8)
    service.add_driver(john)

    anna = Driver("D002", "Anna Driver", "anna@driver.com", "0987654321", "DL-1002")
    anna.set_vehicle(Vehicle("V002", VehicleType.SUV, "XYZ789"))
    anna.set_location(Location("Lower Manhattan", 40.7128, -74.0060))
    anna.update_rating(4.5)
    service.add_driver(anna)

    # Register a rider and add wallet balance
    alice = Rider("P001", "Alice Passenger", "alice@pass.com", "1122334455")
    service.add_wallet_balance(alice, 500.0)

    # Request a ride
    pickup = Location("Times Square", 40.7580, -73.9855)
    dropoff = Location("Central Park", 40.7812, -73.9665)

    ride = service.request_ride(alice, pickup, dropoff)
    if ride is None or ride.driver is None:
        print("No available drivers at the moment.")
        return

    print(f"Ride {ride.ride_id} created")
    plate = ride.driver.vehicle.license_plate if ride.driver.vehicle else "N/A"
    print(f"  Driver : {ride.driver.name} ({plate})")
    print(f"  Fare   : ${ride.fare:.2f}")
    print(f"  Status : {ride.status.value}")

    # Ride lifecycle
    service.start_ride(ride.ride_id)
    print(f"Ride {ride.ride_id} started - status: {ride.status.value}")

    payment = service.complete_ride(ride.ride_id)
    print(f"Ride {ride.ride_id} completed - status: {ride.status.value}")
    if payment is not None:
        print(f"Payment {payment.payment_id}: {payment.status.value} (${payment.amount:.2f})")
    print(f"Rider balance: ${alice.wallet_balance:.2f}")
    print(f"Driver available again: {ride.driver.is_available}")


if __name__ == "__main__":
    main()
