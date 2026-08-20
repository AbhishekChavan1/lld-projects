from datetime import datetime

from ..enums.spot import SpotType
from ..enums.vehicle import VehicleType
from ..enums.payment import PaymentType
from ..models.vehicle import Vehicle
from ..models.parking_spot import ParkingSpot
from ..models.parking_floor import ParkingFloor
from ..models.ticket import Ticket
from ..strategies.pricing import PricingStrategy
from ..payments.payment_factory import PaymentFactory


class ParkingLot:
    def __init__(self, name: str, pricing_strategy: PricingStrategy):
        self.name = name
        self.pricing_strategy = pricing_strategy
        self.floors: list[ParkingFloor] = []
        self.active_tickets: dict[str, Ticket] = {}
        self.ticket_counter = 0

    def add_floor(self, floor: ParkingFloor):
        self.floors.append(floor)

    def park_vehicle(self, vehicle: Vehicle) -> Ticket | None:
        for floor in self.floors:
            spot = floor.find_available_spot(vehicle.vehicle_type)
            if spot:
                if spot.park_vehicle(vehicle):
                    self.ticket_counter += 1
                    ticket = Ticket(spot, vehicle)
                    self.active_tickets[ticket.ticket_id] = ticket
                    return ticket
        return None

    def unpark_vehicle(self, ticket_id: str, payment_type: PaymentType) -> Ticket | None:
        ticket = self.active_tickets.get(ticket_id)
        if ticket is None or not ticket.is_active():
            return None

        ticket.mark_exit()
        ticket.fee = self.pricing_strategy.calculate_price(
            ticket.entry_time, ticket.exit_time
        )

        payment = PaymentFactory.create_payment(payment_type, ticket.fee)
        ticket.paid = payment.process()

        ticket.parking_spot.remove_vehicle()
        del self.active_tickets[ticket_id]
        return ticket

    def get_available_spots(self) -> dict[str, int]:
        result = {}
        for floor in self.floors:
            result[f"Floor {floor.floor_number}"] = floor.get_available_count()
        return result

    def get_total_revenue(self) -> float:
        return sum(t.fee for t in self._completed_tickets)

    @property
    def _completed_tickets(self) -> list[Ticket]:
        return [t for t in self.active_tickets.values() if not t.is_active()]

    def __repr__(self):
        total = sum(f.get_total_count() for f in self.floors)
        available = sum(f.get_available_count() for f in self.floors)
        return f"ParkingLot('{self.name}', available={available}/{total})"
