from abc import ABC, abstractmethod

from flight_alert.models import (
    FlexibleDealResult,
    FlexibleMonthSearch,
)


class FlexibleFlightDealsProvider(ABC):
    """Base interface for flexible flight deals providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    @abstractmethod
    def search(
        self,
        search: FlexibleMonthSearch,
    ) -> FlexibleDealResult:
        """Search for the cheapest matching flexible deal."""
