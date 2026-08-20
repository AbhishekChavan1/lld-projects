from parkinglot.enums.spot import SpotType
from parkinglot.enums.vehicle import VehicleType
from parkinglot.enums.payment import PaymentType
from parkinglot.models.vehicle import Car, Motorcycle, TruckOrBus
from parkinglot.models.parking_spot import ParkingSpot
from parkinglot.models.parking_floor import ParkingFloor
from parkinglot.services.parking_lot import ParkingLot
from parkinglot.strategies.hourly_pricing import HourlyRatePricing
from parkinglot.strategies.flat_pricing import FlatRatePricing
from parkinglot.payments.payment_factory import PaymentFactory


def _build_lot() -> ParkingLot:
    lot = ParkingLot("Test Garage", HourlyRatePricing(hourly_rate=5.0))
    floor = ParkingFloor(1)
    floor.add_parking_spot(ParkingSpot("A1", SpotType.COMPACT))
    floor.add_parking_spot(ParkingSpot("A2", SpotType.COMPACT))
    floor.add_parking_spot(ParkingSpot("B1", SpotType.LARGE))
    floor.add_parking_spot(ParkingSpot("C1", SpotType.TWO_WHEELER))
    floor.add_parking_spot(ParkingSpot("D1", SpotType.HANDICAPPED))
    lot.add_floor(floor)
    return lot


class TestParkingSpot:
    def test_park_available_spot(self):
        spot = ParkingSpot("S1", SpotType.COMPACT)
        car = Car("MH-12-AB-1234")
        assert spot.park_vehicle(car) is True
        assert spot.is_available() is False

    def test_cannot_park_on_occupied_spot(self):
        spot = ParkingSpot("S1", SpotType.COMPACT)
        car1 = Car("MH-12-AB-1234")
        car2 = Car("MH-12-CD-5678")
        spot.park_vehicle(car1)
        assert spot.park_vehicle(car2) is False

    def test_remove_vehicle(self):
        spot = ParkingSpot("S1", SpotType.COMPACT)
        car = Car("MH-12-AB-1234")
        spot.park_vehicle(car)
        removed = spot.remove_vehicle()
        assert removed == car
        assert spot.is_available() is True

    def test_compact_accepts_car_and_motorcycle(self):
        spot = ParkingSpot("S1", SpotType.COMPACT)
        assert spot._is_vehicle_compatible(Car("X")) is True
        assert spot._is_vehicle_compatible(Motorcycle("X")) is True
        assert spot._is_vehicle_compatible(TruckOrBus("X")) is False

    def test_large_rejects_motorcycle(self):
        spot = ParkingSpot("S1", SpotType.LARGE)
        assert spot._is_vehicle_compatible(TruckOrBus("X")) is True
        assert spot._is_vehicle_compatible(Car("X")) is True
        assert spot._is_vehicle_compatible(Motorcycle("X")) is False

    def test_two_wheeler_only_motorcycle(self):
        spot = ParkingSpot("S1", SpotType.TWO_WHEELER)
        assert spot._is_vehicle_compatible(Motorcycle("X")) is True
        assert spot._is_vehicle_compatible(Car("X")) is False


class TestParkingFloor:
    def test_available_count(self):
        floor = ParkingFloor(1)
        floor.add_parking_spot(ParkingSpot("A1", SpotType.COMPACT))
        floor.add_parking_spot(ParkingSpot("A2", SpotType.COMPACT))
        assert floor.get_available_count() == 2

    def test_available_count_after_parking(self):
        floor = ParkingFloor(1)
        spot = ParkingSpot("A1", SpotType.COMPACT)
        floor.add_parking_spot(spot)
        spot.park_vehicle(Car("X"))
        assert floor.get_available_count() == 1


class TestParkingLot:
    def test_park_car(self):
        lot = _build_lot()
        car = Car("MH-12-AB-1234")
        ticket = lot.park_vehicle(car)
        assert ticket is not None
        assert ticket.vehicle == car
        assert ticket.is_active() is True

    def test_park_motorcycle(self):
        lot = _build_lot()
        bike = Motorcycle("MH-12-MOTO-1")
        ticket = lot.park_vehicle(bike)
        assert ticket is not None

    def test_park_truck_uses_large_spot(self):
        lot = _build_lot()
        truck = TruckOrBus("MH-12-TRUCK-1")
        ticket = lot.park_vehicle(truck)
        assert ticket is not None
        assert ticket.parking_spot.spot_type == SpotType.LARGE

    def test_unpark_and_pay(self):
        lot = _build_lot()
        car = Car("MH-12-AB-1234")
        ticket = lot.park_vehicle(car)
        result = lot.unpark_vehicle(ticket.ticket_id, PaymentType.CASH)
        assert result is not None
        assert result.paid is True
        assert result.is_active() is False

    def test_unpark_nonexistent_ticket(self):
        lot = _build_lot()
        assert lot.unpark_vehicle("fake-id", PaymentType.CASH) is None

    def test_lot_full(self):
        lot = _build_lot()
        lot.park_vehicle(Car("C1"))
        lot.park_vehicle(Car("C2"))
        lot.park_vehicle(Motorcycle("M1"))
        lot.park_vehicle(TruckOrBus("T1"))
        lot.park_vehicle(Car("C3"))
        assert lot.park_vehicle(Car("C4")) is None


class TestPricing:
    def test_hourly_pricing(self):
        from datetime import datetime, timedelta
        strategy = HourlyRatePricing(hourly_rate=10.0)
        entry = datetime(2026, 1, 1, 10, 0)
        exit_ = datetime(2026, 1, 1, 13, 0)
        assert strategy.calculate_price(entry, exit_) == 30.0

    def test_flat_pricing(self):
        from datetime import datetime
        strategy = FlatRatePricing(flat_rate=5.0)
        entry = datetime(2026, 1, 1, 10, 0)
        exit_ = datetime(2026, 1, 1, 23, 0)
        assert strategy.calculate_price(entry, exit_) == 5.0


class TestPaymentFactory:
    def test_creates_cash(self):
        p = PaymentFactory.create_payment(PaymentType.CASH, 10.0)
        assert p.process() is True

    def test_creates_card(self):
        p = PaymentFactory.create_payment(PaymentType.CARD, 10.0)
        assert p.process() is True

    def test_creates_upi(self):
        p = PaymentFactory.create_payment(PaymentType.UPI, 10.0)
        assert p.process() is True
