from calendar import monthrange
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class FlexibleMonthSearch:
    """A flexible flight search within a calendar month."""

    origin: str
    destination_name: str
    destination_airports: tuple[str, ...]
    year: int
    month: int
    minimum_trip_days: int
    maximum_trip_days: int
    target_price: Decimal
    direct_only: bool = False
    minimum_alert_drop: Decimal = Decimal("50.00")

    def __post_init__(self) -> None:
        self._validate_airport_code("origin", self.origin)

        if not self.destination_name.strip():
            raise ValueError("Destination name cannot be empty.")

        if not self.destination_airports:
            raise ValueError("At least one destination airport is required.")

        for airport in self.destination_airports:
            self._validate_airport_code(
                "destination airport",
                airport,
            )

        if not 1 <= self.month <= 12:
            raise ValueError("Month must be between 1 and 12.")

        if self.minimum_trip_days < 1:
            raise ValueError("Minimum trip days must be at least one.")

        if self.maximum_trip_days < self.minimum_trip_days:
            raise ValueError("Maximum trip days cannot be lower than minimum trip days.")

        if self.target_price <= Decimal("0"):
            raise ValueError("Target price must be greater than zero.")

        if self.minimum_alert_drop < Decimal("0"):
            raise ValueError("Minimum alert drop cannot be negative.")

    @property
    def outbound_start_date(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def outbound_end_date(self) -> date:
        last_day = monthrange(self.year, self.month)[1]

        return date(self.year, self.month, last_day)

    @property
    def monitor_key(self) -> str:
        """Return a stable identifier for this flexible search."""

        airports = ",".join(sorted(self.destination_airports))

        return "|".join(
            [
                "flexible-month",
                self.origin,
                airports,
                f"{self.year:04d}-{self.month:02d}",
                (f"{self.minimum_trip_days}-{self.maximum_trip_days}"),
                str(int(self.direct_only)),
            ]
        )

    @staticmethod
    def _validate_airport_code(
        field_name: str,
        code: str,
    ) -> None:
        if len(code) != 3 or not code.isalpha() or code != code.upper():
            raise ValueError(f"{field_name.capitalize()} must be a three-letter uppercase code.")
