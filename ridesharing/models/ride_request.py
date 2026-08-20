from models.location import Location
from models.rider import Rider


class RideRequest:
    def __init__(
        self,
        rider: Rider,
        pickup_location: Location,
        dropoff_location: Location,
    ) -> None:
        self.rider = rider
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
