from abc import ABC, abstractmethod


class Startable(ABC):
    @abstractmethod
    def start(self) -> None:
        pass


class Refuelable(ABC):
    @abstractmethod
    def refuel(self) -> None:
        pass


class Rechargeable(ABC):
    @abstractmethod
    def charge(self) -> None:
        pass


class PetrolCar(Startable, Refuelable):
    def start(self) -> None:
        print("[Car] Engine started")

    def refuel(self) -> None:
        print("[Car] Tank filled")


class ElectricScooter(Startable, Rechargeable):
    def start(self) -> None:
        print("[Scooter] Motor engaged silently")

    def charge(self) -> None:
        print("[Scooter] Battery charging at 50kW")


class GarageService:
    def service(self, vehicle: Startable) -> None:
        print("Starting service...")
        vehicle.start()
        if isinstance(vehicle, Refuelable):
            vehicle.refuel()
        elif isinstance(vehicle, Rechargeable):
            vehicle.charge()
        print("Service complete")


def main():
    garage = GarageService()

    car: Startable = PetrolCar()
    scooter: Startable = ElectricScooter()

    garage.service(car)
    garage.service(scooter)


if __name__ == "__main__":
    main()
