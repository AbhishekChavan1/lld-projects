import pytest

from enums.paymentstatus import PaymentStatus
from enums.ridestatus import RideStatus
from enums.vehicletype import VehicleType
from models.driver import Driver
from models.location import Location
from models.ride_request import RideRequest
from models.rider import Rider
from models.vehicle import Vehicle
from services.matching import MatchingService
from services.paymentservices import PaymentService
from services.rideservices import RideService
from strategies.basic_pricing_strategy import BasicPricingStrategy
from strategies.cheapest_driver_strategy import CheapestDriverStrategy
from strategies.highest_rated_driver import HighestRatedDriverStrategy
from strategies.nearest_driver_strategy import NearestDriverStrategy
from strategies.surge_pricing_strategy import SurgePricingStrategy


@pytest.fixture
def locations() -> tuple[Location, Location]:
    pickup = Location("Times Square", 40.7580, -73.9855)
    dropoff = Location("Central Park", 40.7812, -73.9665)
    return pickup, dropoff


@pytest.fixture
def rider() -> Rider:
    rider = Rider("P001", "Alice", "alice@pass.com", "1122334455")
    rider.wallet_balance = 500.0
    return rider


def make_driver(user_id: str, name: str, lat: float, lon: float, rating: float = 4.5) -> Driver:
    driver = Driver(user_id, name, f"{name}@driver.com", "1234567890", f"DL-{user_id}")
    driver.set_vehicle(Vehicle(user_id, VehicleType.CAR, f"PLATE-{user_id}"))
    driver.set_location(Location(name, lat, lon))
    driver.update_rating(rating)
    return driver


def make_request(rider: Rider, pickup: Location, dropoff: Location) -> RideRequest:
    return RideRequest(rider, pickup, dropoff)


class TestModels:
    def test_location_distance_zero(self):
        a = Location("A", 40.7128, -74.0060)
        b = Location("B", 40.7128, -74.0060)
        assert a.distance_to(b) == pytest.approx(0.0, abs=1e-6)

    def test_driver_rating_average(self):
        driver = make_driver("D001", "John", 40.0, -74.0)
        driver.update_rating(5.0)
        assert driver.rating == pytest.approx((4.5 + 5.0) / 2)
        assert len(driver.ride_history) == 0  # ratings must not pollute ride history

    def test_driver_rating_out_of_range(self):
        driver = make_driver("D001", "John", 40.0, -74.0)
        with pytest.raises(ValueError):
            driver.update_rating(6.0)

    def test_driver_get_info(self):
        driver = make_driver("D001", "John", 40.0, -74.0)
        info = driver.get_info()
        assert info["name"] == "John"
        assert info["vehicle"]["license_plate"] == "PLATE-D001"


class TestStrategies:
    def test_nearest_driver(self, locations, rider):
        pickup, dropoff = locations
        far = make_driver("D001", "Far", 40.0, -74.0)
        near = make_driver("D002", "Near", pickup.latitude, pickup.longitude)
        request = make_request(rider, pickup, dropoff)
        assert NearestDriverStrategy().match(request, [far, near]) is near

    def test_cheapest_driver(self, locations, rider):
        pickup, dropoff = locations
        close = make_driver("D001", "Close", pickup.latitude, pickup.longitude)
        far = make_driver("D002", "Far", 40.0, -74.0)
        request = make_request(rider, pickup, dropoff)
        assert CheapestDriverStrategy().match(request, [far, close]) is close

    def test_highest_rated_driver(self, locations, rider):
        pickup, dropoff = locations
        low = make_driver("D001", "Low", pickup.latitude, pickup.longitude, rating=3.0)
        high = make_driver("D002", "High", pickup.latitude, pickup.longitude, rating=5.0)
        request = make_request(rider, pickup, dropoff)
        assert HighestRatedDriverStrategy().match(request, [low, high]) is high

    def test_basic_pricing(self, locations):
        pickup, dropoff = locations
        fare = BasicPricingStrategy(rate_per_km=10.0).calculate_fare(pickup, dropoff)
        assert fare > 0

    def test_surge_pricing(self, locations):
        pickup, dropoff = locations
        basic = BasicPricingStrategy(rate_per_km=10.0)
        surge = SurgePricingStrategy(basic, surge_multiplier=2.0)
        assert surge.calculate_fare(pickup, dropoff) == pytest.approx(
            basic.calculate_fare(pickup, dropoff) * 2.0
        )

    def test_unavailable_driver_skipped(self, locations, rider):
        pickup, dropoff = locations
        offline = make_driver("D001", "Offline", pickup.latitude, pickup.longitude)
        offline.go_offline()
        request = make_request(rider, pickup, dropoff)
        assert NearestDriverStrategy().match(request, [offline]) is None


class TestRideService:
    @staticmethod
    def make_service(strategy=NearestDriverStrategy(), pricing=BasicPricingStrategy()):
        return RideService(
            matching_service=MatchingService(strategy),
            pricing_strategy=pricing,
            payment_service=PaymentService(),
        )

    def test_full_ride_flow(self, locations, rider):
        pickup, dropoff = locations
        service = self.make_service()
        service.add_driver(make_driver("D001", "John", pickup.latitude, pickup.longitude))

        ride = service.request_ride(rider, pickup, dropoff)
        assert ride is not None
        assert ride.status == RideStatus.DRIVER_ASSIGNED
        assert ride.fare > 0

        assert service.start_ride(ride.ride_id) is True
        assert ride.status == RideStatus.DRIVING

        payment = service.complete_ride(ride.ride_id)
        assert ride.status == RideStatus.COMPLETED
        assert payment is not None
        assert payment.status == PaymentStatus.COMPLETED
        assert rider.wallet_balance == pytest.approx(500.0 - ride.fare)

    def test_no_driver_returns_none(self, locations, rider):
        pickup, dropoff = locations
        service = self.make_service()
        assert service.request_ride(rider, pickup, dropoff) is None

    def test_payment_fails_on_insufficient_balance(self, locations):
        pickup, dropoff = locations
        poor_rider = Rider("P001", "Alice", "a@b.com", "123")
        poor_rider.wallet_balance = 0.0
        service = self.make_service()
        service.add_driver(make_driver("D001", "John", pickup.latitude, pickup.longitude))

        ride = service.request_ride(poor_rider, pickup, dropoff)
        assert ride is not None
        service.start_ride(ride.ride_id)
        payment = service.complete_ride(ride.ride_id)
        assert payment is not None
        assert payment.status == PaymentStatus.FAILED

    def test_cancel_ride(self, locations, rider):
        pickup, dropoff = locations
        service = self.make_service()
        driver = make_driver("D001", "John", pickup.latitude, pickup.longitude)
        service.add_driver(driver)

        ride = service.request_ride(rider, pickup, dropoff)
        assert ride is not None
        assert service.cancel_ride(ride.ride_id) is True
        assert ride.status == RideStatus.CANCELLED
        assert driver.is_available is True

    def test_ride_history_tracked(self, locations, rider):
        pickup, dropoff = locations
        service = self.make_service()
        service.add_driver(make_driver("D001", "John", pickup.latitude, pickup.longitude))

        ride = service.request_ride(rider, pickup, dropoff)
        assert ride in rider.ride_history
        assert ride in ride.driver.ride_history

    def test_add_wallet_balance_rejects_non_positive(self, rider):
        service = self.make_service()
        assert service.add_wallet_balance(rider, 0.0) is False
        assert service.add_wallet_balance(rider, -5.0) is False
        assert service.add_wallet_balance(rider, 100.0) is True
