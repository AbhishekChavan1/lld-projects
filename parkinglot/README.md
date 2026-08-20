# Parking Lot

A Python implementation of a parking lot management system demonstrating **Strategy Pattern**, **Factory Pattern**, and **Composition**.

## Features

- Multi-floor parking with mixed spot types (compact, large, handicapped, two-wheeler)
- Vehicle type compatibility checking per spot
- Ticket-based entry/exit tracking
- Pluggable pricing strategies (hourly rate, flat rate)
- Payment factory supporting cash, card, and UPI
- Display board showing real-time availability

## Design Patterns

- **Strategy Pattern** — pricing algorithms (`HourlyRatePricing`, `FlatRatePricing`) are interchangeable
- **Factory Pattern** — `PaymentFactory` creates the correct payment handler
- **Composition** — `ParkingLot` is composed of `ParkingFloor`s, which contain `ParkingSpot`s

## Structure

```
parkinglot/
├── enums/
│   ├── spot.py              # SpotType enum
│   ├── vehicle.py           # VehicleType enum
│   └── payment.py           # PaymentType enum
├── models/
│   ├── vehicle.py           # Vehicle hierarchy (Car, Motorcycle, TruckOrBus)
│   ├── ticket.py            # Parking ticket with entry/exit tracking
│   ├── parking_spot.py      # Spot with availability + compatibility logic
│   └── parking_floor.py     # Floor holding a list of spots
├── services/
│   ├── parking_lot.py       # Core orchestrator (park/unpark/query)
│   └── display_board.py     # Console display of availability
├── payments/
│   ├── payment.py           # Payment ABC
│   ├── payment_factory.py   # Factory for payment types
│   ├── cash.py              # CashPayment
│   ├── card.py              # CardPayment
│   └── upi.py               # UPIPayment
├── strategies/
│   ├── pricing.py           # PricingStrategy ABC
│   ├── hourly_pricing.py    # Rate per hour
│   └── flat_pricing.py      # Fixed rate
├── tests/
│   └── test_parkinglot.py   # 20 pytest tests
├── main.py                  # Demo entry point
└── README.md
```

## Quick Start

```bash
cd parkinglot
python -m parkinglot.main
```

## Running Tests

```bash
pytest parkinglot/tests/
```
