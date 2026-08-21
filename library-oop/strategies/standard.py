from .penalty import Penalty


class StandardPenalty(Penalty):
    def __init__(self, rate_per_day: float = 1.0):
        self.rate_per_day = rate_per_day

    def calculate_fine(self, days_overdue: int) -> float:
        return max(0, days_overdue) * self.rate_per_day
