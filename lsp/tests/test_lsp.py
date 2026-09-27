import pytest

import garage_service
import violation
from garage_service import (
    ElectricScooter,
    GarageService,
    PetrolCar,
    Rechargeable,
    Refuelable,
    Startable,
)
from violation import Vehicle
from violation import ElectricScooter as ViolationScooter
from violation import service as violating_service


@pytest.fixture
def garage():
    return GarageService()


class TestViolation:
    """The anti-pattern: one fat interface forces a bogus implementation."""

    def test_vehicle_is_abstract(self):
        with pytest.raises(TypeError):
            Vehicle()

    def test_scooter_must_implement_refuel(self):
        assert "refuel" in ElectricScooter.__abstractmethods__ or hasattr(
            ViolationScooter, "refuel"
        )

    def test_refuel_raises_not_implemented(self):
        with pytest.raises(NotImplementedError, match="Scooters don't refuel"):
            ViolationScooter().refuel()

    def test_scooter_satisfies_the_abstract_base_despite_being_unusable(self):
        """LSP violation: the type fits the signature but breaks the contract."""
        scooter = ViolationScooter()
        assert isinstance(scooter, Vehicle)

    def test_generic_service_crashes_on_a_valid_substitute(self, capsys):
        with pytest.raises(NotImplementedError):
            violating_service(ViolationScooter())
        assert "Service complete" not in capsys.readouterr().out

    def test_generic_service_is_fine_with_a_petrol_vehicle(self, capsys):
        class PetrolBike(Vehicle):
            def start(self) -> None:
                print("[Bike] Engine started")

            def refuel(self) -> None:
                print("[Bike] Tank filled")

        violating_service(PetrolBike())
        assert "Service complete" in capsys.readouterr().out


class TestCapabilityInterfaces:
    def test_capability_abcs_are_separate(self):
        assert Refuelable is not Rechargeable
        assert not issubclass(Refuelable, Rechargeable)
        assert not issubclass(Rechargeable, Refuelable)

    def test_petrol_car_is_startable_and_refuelable_only(self):
        car = PetrolCar()
        assert isinstance(car, Startable)
        assert isinstance(car, Refuelable)
        assert not isinstance(car, Rechargeable)

    def test_scooter_is_startable_and_rechargeable_only(self):
        scooter = ElectricScooter()
        assert isinstance(scooter, Startable)
        assert isinstance(scooter, Rechargeable)
        assert not isinstance(scooter, Refuelable)

    def test_every_vehicle_can_start(self, garage, capsys):
        garage.service(PetrolCar())
        garage.service(ElectricScooter())
        assert capsys.readouterr().out.count("Starting service...") == 2


class TestGarageService:
    def test_services_a_petrol_vehicle(self, garage, capsys):
        garage.service(PetrolCar())
        out = capsys.readouterr().out
        assert "[Car] Engine started" in out
        assert "[Car] Tank filled" in out
        assert "Service complete" in out

    def test_services_an_electric_vehicle(self, garage, capsys):
        garage.service(ElectricScooter())
        out = capsys.readouterr().out
        assert "[Scooter] Motor engaged silently" in out
        assert "[Scooter] Battery charging at 50kW" in out
        assert "Tank filled" not in out
        assert "Service complete" in out

    def test_startable_only_vehicle_is_still_serviced(self, garage, capsys):
        class Lawnmower(Startable):
            def start(self) -> None:
                print("[Mower] Pull started")

        garage.service(Lawnmower())
        out = capsys.readouterr().out
        assert "[Mower] Pull started" in out
        assert "Service complete" in out

    def test_hybrid_is_refuelled_not_charged(self, garage, capsys):
        class HybridCar(Startable, Refuelable, Rechargeable):
            def start(self) -> None:
                print("[Hybrid] Started")

            def refuel(self) -> None:
                print("[Hybrid] Tank filled")

            def charge(self) -> None:
                print("[Hybrid] Battery charging")

        garage.service(HybridCar())
        out = capsys.readouterr().out
        assert "Tank filled" in out
        assert "Battery charging" not in out

    def test_no_substitution_ever_raises(self, garage):
        for vehicle in (PetrolCar(), ElectricScooter()):
            garage.service(vehicle)


class TestSubstitutability:
    def test_every_vehicle_is_interchangeable_behind_startable(self, garage, capsys):
        vehicles: list[Startable] = [PetrolCar(), ElectricScooter()]
        for vehicle in vehicles:
            garage.service(vehicle)
        out = capsys.readouterr().out
        assert "Starting service..." in out
        assert "Service complete" in out

    def test_capability_discovery_uses_no_renaming(self):
        """Each capability keeps its natural name; no NotImplemented stubs."""
        assert hasattr(PetrolCar(), "refuel")
        assert hasattr(ElectricScooter(), "charge")
        assert not hasattr(ElectricScooter(), "refuel")

    def test_fixed_design_has_no_not_implemented_stubs(self):
        for cls in (PetrolCar, ElectricScooter, Refuelable, Rechargeable, Startable):
            source = __import__("inspect").getsource(cls)
            assert "NotImplementedError" not in source

    def test_fixed_and_violating_scooters_behave_the_same_on_start(self, capsys):
        garage_service.ElectricScooter().start()
        ViolationScooter().start()
        assert capsys.readouterr().out.count("[Scooter] Motor engaged silently") == 2
