from dataclasses import dataclass
from decimal import Decimal

from flight_alert.models.price_result import PriceResult


@dataclass(frozen=True, slots=True)
class PriceHistoryAnalysis:
    """Comparison between the current and previously recorded prices."""

    result: PriceResult
    previous_price: Decimal | None
    previous_lowest_price: Decimal | None
    change_amount: Decimal | None
    change_percentage: Decimal | None
    is_new_lowest: bool
