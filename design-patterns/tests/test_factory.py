"""Tests for Factory Pattern implementations."""
import pytest
from factory.parking_spot_factory import (
    ParkingSpotFactory,
    ParkingSpot,
    CarSpot,
    BikeSpot,
    TruckSpot,
    SpotType,
)
from factory.notification_factory import (
    NotificationChannelFactory,
    NotificationChannel,
    EmailChannel,
    SMSChannel,
    PushChannel,
    ChannelType,
    EmailCreator,
    SMSCreator,
)


class TestParkingSpotFactory:
    """Tests for simple factory - parking spots."""

    def test_create_car_spot(self):
        spot = ParkingSpotFactory.create_spot(SpotType.CAR, "A1")
        assert isinstance(spot, CarSpot)
        assert spot.spot_id == "A1"
        assert spot.get_hourly_rate() == 20.0
        assert spot.get_size() == "medium"

    def test_create_bike_spot(self):
        spot = ParkingSpotFactory.create_spot(SpotType.BIKE, "B1")
        assert isinstance(spot, BikeSpot)
        assert spot.get_hourly_rate() == 10.0

    def test_create_truck_spot(self):
        spot = ParkingSpotFactory.create_spot(SpotType.TRUCK, "C1")
        assert isinstance(spot, TruckSpot)
        assert spot.get_hourly_rate() == 40.0

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown spot type"):
            ParkingSpotFactory.create_spot("airplane", "X1")

    def test_park_and_remove(self):
        spot = ParkingSpotFactory.create_spot(SpotType.CAR, "A1")
        assert spot.park("vehicle_1") is True
        assert spot.occupied is True
        assert spot.park("vehicle_2") is False

        removed = spot.remove_vehicle()
        assert removed == "vehicle_1"
        assert spot.occupied is False

    def test_supported_types(self):
        types = ParkingSpotFactory.supported_types()
        assert SpotType.CAR in types
        assert SpotType.BIKE in types
        assert SpotType.TRUCK in types

    def test_all_spots_are_parking_spot(self):
        for spot_type in SpotType:
            spot = ParkingSpotFactory.create_spot(spot_type, "X")
            assert isinstance(spot, ParkingSpot)


class TestNotificationChannelFactory:
    """Tests for factory method - notification channels."""

    def test_create_email(self):
        channel = NotificationChannelFactory.create(ChannelType.EMAIL)
        assert isinstance(channel, EmailChannel)
        result = channel.send("user@test.com", "Hello")
        assert "EMAIL" in result
        assert "user@test.com" in result

    def test_create_sms(self):
        channel = NotificationChannelFactory.create(ChannelType.SMS)
        assert isinstance(channel, SMSChannel)
        result = channel.send("+123456", "Hello")
        assert "SMS" in result

    def test_create_push(self):
        channel = NotificationChannelFactory.create(ChannelType.PUSH)
        assert isinstance(channel, PushChannel)
        result = channel.send("device_token", "Hello")
        assert "PUSH" in result

    def test_unknown_channel_raises(self):
        with pytest.raises(ValueError, match="Unknown channel type"):
            NotificationChannelFactory.create("carrier_pigeon")

    def test_supported_channels(self):
        channels = NotificationChannelFactory.supported_channels()
        assert ChannelType.EMAIL in channels
        assert ChannelType.SMS in channels
        assert ChannelType.PUSH in channels

    def test_factory_method_creator_email(self):
        creator = EmailCreator(smtp_host="custom.smtp.com")
        channel = creator.create_channel()
        assert isinstance(channel, EmailChannel)
        assert channel.smtp_host == "custom.smtp.com"

    def test_factory_method_creator_sms(self):
        creator = SMSCreator(provider="Vonage")
        channel = creator.create_channel()
        assert isinstance(channel, SMSChannel)
        assert channel.provider == "Vonage"

    def test_factory_method_send_notification(self):
        creator = EmailCreator()
        result = creator.send_notification("user@test.com", "Welcome!")
        assert "EMAIL" in result
        assert "user@test.com" in result
        assert "Welcome!" in result
