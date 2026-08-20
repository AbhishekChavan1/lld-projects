import uuid
from datetime import datetime

from .parking_spot import ParkingSpot
from .vehicle import Vehicle


class Ticket:
    def __init__(self, parking_spot: ParkingSpot, vehicle: Vehicle):
        self.ticket_id = str(uuid.uuid4())[:8]
        self.parking_spot = parking_spot
        self.vehicle = vehicle
        self.entry_time = datetime.now()
        self.exit_time: datetime | None = None
        self.fee: float = 0.0
        self.paid: bool = False

    def mark_exit(self):
        self.exit_time = datetime.now()

    def is_active(self) -> bool:
        return self.exit_time is None

    def __repr__(self):
        return (
            f"Ticket(id='{self.ticket_id}', vehicle={self.vehicle}, "
            f"spot='{self.parking_spot.spot_id}', active={self.is_active()})"
        )
