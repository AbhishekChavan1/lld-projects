from .parking_spot import ParkingSpot


class ParkingFloor:
    def __init__(self, floor_number: int):
        self.floor_number = floor_number
        self.parking_spots: list[ParkingSpot] = []

    def add_parking_spot(self, spot: ParkingSpot):
        self.parking_spots.append(spot)

    def get_available_spots(self) -> list[ParkingSpot]:
        return [s for s in self.parking_spots if s.is_available()]

    def get_available_count(self) -> int:
        return len(self.get_available_spots())

    def get_total_count(self) -> int:
        return len(self.parking_spots)

    def find_available_spot(self, vehicle_type) -> ParkingSpot | None:
        for spot in self.parking_spots:
            if spot.is_available() and spot._is_vehicle_compatible(
                _StubVehicle(vehicle_type)
            ):
                return spot
        return None

    def __repr__(self):
        return (
            f"ParkingFloor(floor={self.floor_number}, "
            f"available={self.get_available_count()}/{self.get_total_count()})"
        )


class _StubVehicle:
    """Lightweight wrapper to check spot compatibility without a full Vehicle."""

    def __init__(self, vehicle_type):
        self.vehicle_type = vehicle_type
