from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from flight_alert.models.flexible_month_search import (
    FlexibleMonthSearch,
)


@dataclass(frozen=True, slots=True)
class FlexibleDealResult:
    """The cheapest matching deal from a flexible search."""

    search: FlexibleMonthSearch
    price: Decimal
    origin: str
    destination: str
    departure_date: date
    return_date: date
    airline: str
    source: str
    booking_url: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.price <= Decimal("0"):
            raise ValueError("Deal price must be greater than zero.")

        if self.return_date < self.departure_date:
            raise ValueError("Deal return date cannot be before departure date.")

        if self.destination not in self.search.destination_airports:
            raise ValueError("Deal destination is not allowed by the search.")

        if not self.airline.strip():
            raise ValueError("Airline cannot be empty.")

    @property
    def trip_days(self) -> int:
        return (self.return_date - self.departure_date).days
