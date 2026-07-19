from abc import ABC, abstractmethod

from flight_alert.models import (
    FlexibleDateOption,
    FlexibleDealResult,
    FlexibleMonthSearch,
)


class FlexibleFlightDealsProvider(ABC):
    """Base interface for rotating flexible searches."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    @abstractmethod
    def search(
        self,
        search: FlexibleMonthSearch,
        date_option: FlexibleDateOption,
    ) -> FlexibleDealResult:
        """Search one exact combination from the date grid."""
