from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from flight_alert.models.route import Route


@dataclass(frozen=True, slots=True)
class PriceResult:
    """A flight price returned by a provider."""

    route: Route
    price: Decimal
    airline: str
    source: str
    booking_url: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if self.price <= Decimal("0"):
            raise ValueError("Price must be greater than zero.")

        if not self.airline.strip():
            raise ValueError("Airline cannot be empty.")

        if not self.source.strip():
            raise ValueError("Source cannot be empty.")
