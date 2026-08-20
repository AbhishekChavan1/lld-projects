from datetime import datetime
from typing import Optional

from enums.ridestatus import RideStatus
from models.driver import Driver
from models.location import Location
from models.rider import Rider


class Ride:
    def __init__(
        self,
        ride_id: str,
        rider: Rider,
        driver: Optional[Driver],
        pickup_location: Location,
        dropoff_location: Location,
        fare: float = 0.0,
    ) -> None:
        self.ride_id = ride_id
        self.rider = rider
        self.driver: Optional[Driver] = driver
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.status = RideStatus.REQUESTED
        self.fare = fare
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def assign_driver(self, driver: Driver) -> None:
        """Assign a driver to the ride."""
        if self.status != RideStatus.REQUESTED:
            raise ValueError("Driver can only be assigned to a requested ride.")
        self.driver = driver
        self.status = RideStatus.DRIVER_ASSIGNED

    def start(self) -> None:
        """Start the ride."""
        if self.status != RideStatus.DRIVER_ASSIGNED:
            raise ValueError("Cannot start ride. Driver must be assigned first.")
        self.status = RideStatus.DRIVING
        self.started_at = datetime.now()

    def complete(self) -> None:
        """Complete the ride."""
        if self.status != RideStatus.DRIVING:
            raise ValueError("Cannot complete ride. Ride must be in progress.")
        self.status = RideStatus.COMPLETED
        self.completed_at = datetime.now()

    def cancel(self) -> None:
        """Cancel the ride."""
        if self.status not in (RideStatus.REQUESTED, RideStatus.DRIVER_ASSIGNED, RideStatus.DRIVING):
            raise ValueError("Cannot cancel ride. Ride already finished.")
        self.status = RideStatus.CANCELLED

    def update_status(self, new_status: RideStatus) -> None:
        """Update the ride status directly."""
        if not isinstance(new_status, RideStatus):
            raise ValueError("Invalid status value. Must be an instance of RideStatus.")
        self.status = new_status
