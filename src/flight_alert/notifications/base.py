from abc import ABC, abstractmethod

from flight_alert.models import PriceAnalysis, PriceHistoryAnalysis


class PriceAlertNotifier(ABC):
    """Base interface for price alert notifiers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the notification channel name."""

    @abstractmethod
    def send(
        self,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
    ) -> None:
        """Send a flight price alert."""
