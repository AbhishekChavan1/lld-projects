from parkinglot.enums.spot import SpotType
from parkinglot.enums.payment import PaymentType
from parkinglot.models.vehicle import Car, Motorcycle, TruckOrBus
from parkinglot.models.parking_spot import ParkingSpot
from parkinglot.models.parking_floor import ParkingFloor
from parkinglot.services.parking_lot import ParkingLot
from parkinglot.services.display_board import DisplayBoard
from parkinglot.strategies.hourly_pricing import HourlyRatePricing


def main():
    lot = ParkingLot("City Center Garage", HourlyRatePricing(hourly_rate=4.0))

    floor1 = ParkingFloor(1)
    for i in range(3):
        floor1.add_parking_spot(ParkingSpot(f"1A-{i+1}", SpotType.COMPACT))
    for i in range(2):
        floor1.add_parking_spot(ParkingSpot(f"1B-{i+1}", SpotType.LARGE))
    floor1.add_parking_spot(ParkingSpot("1C-1", SpotType.TWO_WHEELER))
    floor1.add_parking_spot(ParkingSpot("1D-1", SpotType.HANDICAPPED))
    lot.add_floor(floor1)

    floor2 = ParkingFloor(2)
    for i in range(4):
        floor2.add_parking_spot(ParkingSpot(f"2A-{i+1}", SpotType.COMPACT))
    for i in range(3):
        floor2.add_parking_spot(ParkingSpot(f"2B-{i+1}", SpotType.LARGE))
    lot.add_floor(floor2)

    board = DisplayBoard(lot)
    board.show_availability()

    print("--- Parking vehicles ---")
    vehicles = [
        Car("MH-12-AB-1234"),
        Car("MH-14-CD-5678"),
        Motorcycle("KA-01-MOTO-1"),
        TruckOrBus("GJ-05-BUS-99"),
        Car("MH-12-EF-3456"),
        Motorcycle("DL-10-BIKE-2"),
    ]

    tickets = []
    for v in vehicles:
        ticket = lot.park_vehicle(v)
        if ticket:
            print(f"  Parked {v} -> Spot {ticket.parking_spot.spot_id}  [ticket: {ticket.ticket_id}]")
            tickets.append(ticket)
        else:
            print(f"  REJECTED {v} — lot full")

    board.show_availability()

    print("--- Unparking vehicles ---")
    for ticket in tickets[:3]:
        result = lot.unpark_vehicle(ticket.ticket_id, PaymentType.CARD)
        if result:
            print(f"  Unparked {result.vehicle} from {result.parking_spot.spot_id}  fee: ${result.fee:.2f}")

    board.show_availability()

    print(f"\n  Total vehicles still parked: {len(lot.active_tickets)}")


if __name__ == "__main__":
    main()
