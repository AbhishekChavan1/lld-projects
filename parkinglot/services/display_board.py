from ..services.parking_lot import ParkingLot
from ..enums.vehicle import VehicleType


class DisplayBoard:
    def __init__(self, parking_lot: ParkingLot):
        self.parking_lot = parking_lot

    def show_availability(self):
        print(f"\n{'=' * 45}")
        print(f"  {self.parking_lot.name} — Spot Availability")
        print(f"{'=' * 45}")
        for floor in self.parking_lot.floors:
            counts = {}
            for spot in floor.parking_spots:
                key = spot.spot_type.value
                if key not in counts:
                    counts[key] = {"total": 0, "free": 0}
                counts[key]["total"] += 1
                if spot.is_available():
                    counts[key]["free"] += 1

            print(f"\n  Floor {floor.floor_number}:")
            for spot_type, c in counts.items():
                print(f"    {spot_type:15s} — {c['free']:>2} / {c['total']:>2} available")
        print(f"{'=' * 45}\n")
