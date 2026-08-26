"""
Factory Pattern - Parking Spot Factory (Simple Factory)

Centralizes creation logic for parking spots. Instead of scattering
if/else chains everywhere, one factory creates the right type.

Where this fits in LLD:
- Parking Lot: ParkingSpotFactory.create_spot(type, id)
- Each spot type has different hourly rate and size constraints
- Client code never references concrete spot classes directly

From The Design Round:
"Every if-else chain repeated wherever spots are needed."
The factory eliminates this duplication.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum


class SpotType(Enum):
    CAR = "car"
    BIKE = "bike"
    TRUCK = "truck"


class ParkingSpot(ABC):
    """Abstract product - all parking spots share this interface."""

    def __init__(self, spot_id: str) -> None:
        self.spot_id = spot_id
        self.occupied = False

    @abstractmethod
    def get_hourly_rate(self) -> float:
        ...

    @abstractmethod
    def get_size(self) -> str:
        ...

    def park(self, vehicle_id: str) -> bool:
        if self.occupied:
            return False
        self.occupied = True
        self._vehicle_id = vehicle_id
        return True

    def remove_vehicle(self) -> str | None:
        if not self.occupied:
            return None
        vehicle_id = self._vehicle_id
        self.occupied = False
        self._vehicle_id = ""
        return vehicle_id

    def __repr__(self) -> str:
        status = "OCCUPIED" if self.occupied else "EMPTY"
        return f"{self.__class__.__name__}(id='{self.spot_id}', status={status})"


class CarSpot(ParkingSpot):
    def get_hourly_rate(self) -> float:
        return 20.0

    def get_size(self) -> str:
        return "medium"


class BikeSpot(ParkingSpot):
    def get_hourly_rate(self) -> float:
        return 10.0

    def get_size(self) -> str:
        return "small"


class TruckSpot(ParkingSpot):
    def get_hourly_rate(self) -> float:
        return 40.0

    def get_size(self) -> str:
        return "large"


class ParkingSpotFactory:
    """
    Simple Factory - one class, one create method.
    Uses a registry dict instead of if/else for easy extension.
    """

    _registry: dict[SpotType, type[ParkingSpot]] = {
        SpotType.CAR: CarSpot,
        SpotType.BIKE: BikeSpot,
        SpotType.TRUCK: TruckSpot,
    }

    @classmethod
    def create_spot(cls, spot_type: SpotType, spot_id: str) -> ParkingSpot:
        spot_class = cls._registry.get(spot_type)
        if spot_class is None:
            raise ValueError(f"Unknown spot type: {spot_type}")
        return spot_class(spot_id)

    @classmethod
    def register(cls, spot_type: SpotType, spot_class: type[ParkingSpot]) -> None:
        cls._registry[spot_type] = spot_class

    @classmethod
    def supported_types(cls) -> list[SpotType]:
        return list(cls._registry.keys())
