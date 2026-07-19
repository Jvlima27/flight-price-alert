from abc import ABC, abstractmethod

from flight_alert.models import (
    AlertDecision,
    PriceAnalysis,
    PriceHistoryAnalysis,
)


class PriceInsightGenerator(ABC):
    """Base interface for AI-powered price insights."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the insight generator name."""

    @abstractmethod
    def generate(
        self,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
        alert_decision: AlertDecision,
    ) -> str:
        """Generate a concise explanation for a price alert."""
