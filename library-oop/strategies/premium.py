from .penalty import Penalty


class PremiumPenalty(Penalty):
    def __init__(self, daily_rate: float = 1.0, grace_days: int = 5):
        self.daily_rate = daily_rate
        self.grace_days = grace_days

    def calculate_fine(self, days_overdue: int) -> float:
        days_overdue = max(0, days_overdue)
        if days_overdue <= self.grace_days:
            return days_overdue * self.daily_rate
        first_days = self.grace_days * self.daily_rate
        remaining = (days_overdue - self.grace_days) * self.daily_rate * 2
        return first_days + remaining
