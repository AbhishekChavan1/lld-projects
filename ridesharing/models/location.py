import math


class Location:
    def __init__(self, name: str, latitude: float, longitude: float) -> None:
        self.name = name
        self.latitude = latitude
        self.longitude = longitude

    def distance_to(self, other: "Location") -> float:
        """Haversine distance in kilometers to another location."""
        radius = 6371  # Earth radius in kilometers
        dlat = math.radians(other.latitude - self.latitude)
        dlon = math.radians(other.longitude - self.longitude)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(self.latitude))
            * math.cos(math.radians(other.latitude))
            * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c

    def __repr__(self) -> str:
        return (
            f"Location(name={self.name}, "
            f"latitude={self.latitude}, longitude={self.longitude})"
        )
