from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from flight_alert.models.price_result import PriceResult


class PriceStatus(StrEnum):
    """Classification of a price compared with its target."""

    BELOW_TARGET = "below_target"
    AT_TARGET = "at_target"
    ABOVE_TARGET = "above_target"


@dataclass(frozen=True, slots=True)
class PriceAnalysis:
    """Analysis of a flight price compared with its target."""

    result: PriceResult
    status: PriceStatus
    difference: Decimal
    difference_percentage: Decimal
    should_alert: bool

    @property
    def target_price(self) -> Decimal:
        return self.result.route.target_price
