from ..enums.vehicle import VehicleType


class Vehicle:
    def __init__(self, vehicle_type: VehicleType, license_plate: str):
        self.vehicle_type = vehicle_type
        self.license_plate = license_plate

    def __repr__(self):
        return f"{self.__class__.__name__}(plate='{self.license_plate}')"


class Car(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(VehicleType.CAR, license_plate)


class Motorcycle(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(VehicleType.MOTORCYCLE, license_plate)


class TruckOrBus(Vehicle):
    def __init__(self, license_plate: str):
        super().__init__(VehicleType.TRUCK_OR_BUS, license_plate)
