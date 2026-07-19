from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from flight_alert.models.route import Route


@dataclass(frozen=True, slots=True)
class PriceResult:
    """A flight price returned by a provider."""

    route: Route
    price: Decimal
    airline: str
    source: str
    monitor_key: str | None = None
    booking_url: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.price <= Decimal("0"):
            raise ValueError("Price must be greater than zero.")

        if not self.airline.strip():
            raise ValueError("Airline cannot be empty.")

        if not self.source.strip():
            raise ValueError("Source cannot be empty.")

        if self.monitor_key is not None and not self.monitor_key.strip():
            raise ValueError("Monitor key cannot be empty.")
