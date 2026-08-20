from ..enums.spot import SpotType
from ..enums.vehicle import VehicleType
from .vehicle import Vehicle


class ParkingSpot:
    def __init__(self, spot_id: str, spot_type: SpotType):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.vehicle: Vehicle | None = None

    def is_available(self) -> bool:
        return self.vehicle is None

    def park_vehicle(self, vehicle: Vehicle) -> bool:
        if self.is_available() and self._is_vehicle_compatible(vehicle):
            self.vehicle = vehicle
            return True
        return False

    def remove_vehicle(self) -> Vehicle | None:
        if not self.is_available():
            removed = self.vehicle
            self.vehicle = None
            return removed
        return None

    def _is_vehicle_compatible(self, vehicle: Vehicle) -> bool:
        compatibility = {
            SpotType.COMPACT: {VehicleType.CAR, VehicleType.MOTORCYCLE},
            SpotType.LARGE: {VehicleType.CAR, VehicleType.TRUCK_OR_BUS},
            SpotType.HANDICAPPED: {VehicleType.CAR},
            SpotType.TWO_WHEELER: {VehicleType.MOTORCYCLE},
        }
        return vehicle.vehicle_type in compatibility.get(self.spot_type, set())

    def __repr__(self):
        status = "available" if self.is_available() else "occupied"
        return f"ParkingSpot(id='{self.spot_id}', type={self.spot_type.value}, {status})"
