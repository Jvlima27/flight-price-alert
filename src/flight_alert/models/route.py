from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Route:
    """A flight route that should be monitored."""

    origin: str
    destination: str
    departure_date: date
    target_price: Decimal
    return_date: date | None = None
    direct_only: bool = False
    minimum_alert_drop: Decimal = Decimal("50.00")

    def __post_init__(self) -> None:
        self._validate_location_code("origin", self.origin)
        self._validate_location_code("destination", self.destination)

        if self.origin == self.destination:
            raise ValueError("Origin and destination must be different.")

        if self.target_price <= Decimal("0"):
            raise ValueError("Target price must be greater than zero.")

        if self.minimum_alert_drop < Decimal("0"):
            raise ValueError("Minimum alert drop cannot be negative.")

        if self.return_date is not None and self.return_date < self.departure_date:
            raise ValueError("Return date cannot be before departure date.")

    @staticmethod
    def _validate_location_code(
        field_name: str,
        code: str,
    ) -> None:
        if len(code) != 3 or not code.isalpha() or code != code.upper():
            raise ValueError(f"{field_name.capitalize()} must be a three-letter uppercase code.")
