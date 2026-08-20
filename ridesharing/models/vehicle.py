from enums.vehicletype import VehicleType


class Vehicle:
    def __init__(self, vehicle_id: str, vehicle_type: VehicleType, license_plate: str) -> None:
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate

    def get_info(self) -> dict:
        return {
            "vehicle_id": self.vehicle_id,
            "vehicle_type": self.vehicle_type.value,
            "license_plate": self.license_plate,
        }
