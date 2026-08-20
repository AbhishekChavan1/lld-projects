from typing import Dict, List, Optional

from models.driver import Driver
from models.location import Location
from models.payment import Payment
from models.ride import Ride
from models.ride_request import RideRequest
from models.rider import Rider
from services.matching import MatchingService
from services.paymentservices import PaymentService
from strategies.pricing_strategy import PricingStrategy


class RideService:
    """Coordinates driver matching, fare calculation and payments for rides."""

    def __init__(
        self,
        matching_service: MatchingService,
        pricing_strategy: PricingStrategy,
        payment_service: PaymentService,
    ) -> None:
        self.matching_service = matching_service
        self.pricing_strategy = pricing_strategy
        self.payment_service = payment_service

        self.drivers: List[Driver] = []
        self.rides: Dict[str, Ride] = {}
        self.completed_rides: List[Ride] = []
        self.ride_counter = 0

    def add_driver(self, driver: Driver) -> None:
        self.drivers.append(driver)

    def request_ride(
        self, rider: Rider, pickup_location: Location, dropoff_location: Location
    ) -> Optional[Ride]:
        """Match a driver and create a new ride."""
        ride_request = RideRequest(rider, pickup_location, dropoff_location)
        driver = self.matching_service.find_driver(ride_request, self.drivers)
        if driver is None:
            return None

        self.ride_counter += 1
        ride = Ride(
            ride_id=f"RIDE-{self.ride_counter:04d}",
            rider=rider,
            driver=None,
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            fare=self.pricing_strategy.calculate_fare(pickup_location, dropoff_location),
        )
        ride.assign_driver(driver)

        driver.set_availability(False)
        driver.add_ride(ride)
        rider.ride_history.append(ride)
        self.rides[ride.ride_id] = ride

        return ride

    def start_ride(self, ride_id: str) -> bool:
        ride = self.rides.get(ride_id)
        if ride is None:
            return False
        try:
            ride.start()
            return True
        except ValueError:
            return False

    def complete_ride(self, ride_id: str) -> Optional[Payment]:
        ride = self.rides.get(ride_id)
        if ride is None:
            return None
        try:
            ride.complete()
        except ValueError:
            return None

        payment = self.payment_service.process_payment(ride.rider, ride.fare)
        if ride.driver is not None:
            ride.driver.set_availability(True)

        self.completed_rides.append(ride)
        self.rides.pop(ride_id)
        return payment

    def cancel_ride(self, ride_id: str) -> bool:
        ride = self.rides.get(ride_id)
        if ride is None:
            return False
        try:
            ride.cancel()
        except ValueError:
            return False
        if ride.driver is not None:
            ride.driver.set_availability(True)
        self.rides.pop(ride_id)
        return True

    def add_wallet_balance(self, rider: Rider, amount: float) -> bool:
        if amount <= 0:
            return False
        rider.wallet_balance += amount
        return True
