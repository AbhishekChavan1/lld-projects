from typing import Optional

from models.location import Location
from models.user import User
from models.vehicle import Vehicle


class Driver(User):
    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        phone_number: str,
        license_number: str,
    ) -> None:
        super().__init__(user_id, name, email, phone_number)
        self.license_number = license_number
        self.ride_history: list = []  # Rides driven by the driver
        self.ratings: list[float] = []  # Raw ratings received by the driver
        self.rating: float = 0.0  # Average rating of the driver
        self.vehicle: Optional[Vehicle] = None  # Vehicle associated with the driver
        self.is_available: bool = True  # Availability status of the driver
        self.location: Optional[Location] = None  # Current location of the driver

    @property
    def current_location(self) -> Optional[Location]:
        """Alias for the driver's current location."""
        return self.location

    def update_rating(self, new_rating: float) -> None:
        """Update the driver's average rating based on new feedback."""
        if not 0 <= new_rating <= 5:
            raise ValueError("Rating must be between 0 and 5.")
        self.ratings.append(new_rating)
        self.rating = sum(self.ratings) / len(self.ratings)

    def add_ride(self, ride) -> None:
        """Add a ride to the driver's ride history."""
        self.ride_history.append(ride)

    def set_vehicle(self, vehicle: Vehicle) -> None:
        """Associate a vehicle with the driver."""
        self.vehicle = vehicle

    def set_availability(self, is_available: bool) -> None:
        """Set the driver's availability status."""
        self.is_available = is_available

    def set_location(self, location: Location) -> None:
        """Update the driver's current location."""
        self.location = location

    def get_info(self) -> dict:
        """Return a dictionary containing the driver's information."""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "license_number": self.license_number,
            "rating": self.rating,
            "is_available": self.is_available,
            "location": self.location,
            "vehicle": self.vehicle.get_info() if self.vehicle else None,
        }

    def go_online(self) -> None:
        """Set the driver as available for rides."""
        self.is_available = True

    def go_offline(self) -> None:
        """Set the driver as unavailable for rides."""
        self.is_available = False
