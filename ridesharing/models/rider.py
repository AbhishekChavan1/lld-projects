from models.user import User


class Rider(User):
    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        phone_number: str,
        rating: float = 0.0,
    ) -> None:
        super().__init__(user_id, name, email, phone_number)
        self.rating: float = rating
        self.ride_history: list = []  # History of rides taken by the rider
        self.wallet_balance: float = 0.0  # Available balance used to pay for rides
