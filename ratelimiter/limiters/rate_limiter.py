from abc import ABC, abstractmethod

class RateLimiter(ABC):
    @abstractmethod
    def is_allowed(self, key: str) -> bool:
        """
        Check if the request for the given key is allowed based on the rate limiting rules.

        :param key: The unique identifier for the request (e.g., user ID, IP address).
        :return: True if the request is allowed, False otherwise.
        """
        pass
    