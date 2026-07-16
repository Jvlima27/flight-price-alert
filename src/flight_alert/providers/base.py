from abc import ABC, abstractmethod

from flight_alert.models import PriceResult, Route


class FlightPriceProvider(ABC):
    """Base interface for flight price providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    @abstractmethod
    def search(self, route: Route) -> PriceResult:
        """Search for the best available price for a route."""
