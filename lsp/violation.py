from abc import ABC, abstractmethod


class Vehicle(ABC):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def refuel(self) -> None:
        pass


class ElectricScooter(Vehicle):
    def start(self) -> None:
        print("[Scooter] Motor engaged silently")

    def refuel(self) -> None:
        raise NotImplementedError("Scooters don't refuel")


def service(vehicle: Vehicle) -> None:
    print("Starting service...")
    vehicle.start()
    vehicle.refuel()
    print("Service complete")


def main():
    try:
        service(ElectricScooter())
    except NotImplementedError as e:
        print(f"[Main] Crashed while servicing scooter: {e}")


if __name__ == "__main__":
    main()
