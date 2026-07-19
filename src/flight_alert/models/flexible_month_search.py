from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from flight_alert.models.flexible_date_option import (
    FlexibleDateOption,
)


@dataclass(frozen=True, slots=True)
class FlexibleMonthSearch:
    """A rotating grid of flight dates within a calendar month."""

    origin: str
    destination_name: str
    destination_airports: tuple[str, ...]
    year: int
    month: int
    departure_days: tuple[int, ...]
    trip_lengths: tuple[int, ...]
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

        if len(set(self.destination_airports)) != len(self.destination_airports):
            raise ValueError("Destination airports cannot contain duplicates.")

        if not 1 <= self.month <= 12:
            raise ValueError("Month must be between 1 and 12.")

        if not self.departure_days:
            raise ValueError("At least one departure day is required.")

        if len(set(self.departure_days)) != len(self.departure_days):
            raise ValueError("Departure days cannot contain duplicates.")

        last_day = monthrange(self.year, self.month)[1]

        for departure_day in self.departure_days:
            if not 1 <= departure_day <= last_day:
                raise ValueError(
                    f"Departure day must be between 1 and {last_day} for the selected month."
                )

        if not self.trip_lengths:
            raise ValueError("At least one trip length is required.")

        if len(set(self.trip_lengths)) != len(self.trip_lengths):
            raise ValueError("Trip lengths cannot contain duplicates.")

        if any(length < 1 for length in self.trip_lengths):
            raise ValueError("Every trip length must be at least one day.")

        if self.target_price <= Decimal("0"):
            raise ValueError("Target price must be greater than zero.")

        if self.minimum_alert_drop < Decimal("0"):
            raise ValueError("Minimum alert drop cannot be negative.")

    @property
    def date_options(self) -> tuple[FlexibleDateOption, ...]:
        """Return every configured date combination."""

        options: list[FlexibleDateOption] = []

        for departure_day in sorted(self.departure_days):
            departure_date = date(
                self.year,
                self.month,
                departure_day,
            )

            for trip_length in sorted(self.trip_lengths):
                options.append(
                    FlexibleDateOption(
                        departure_date=departure_date,
                        return_date=(departure_date + timedelta(days=trip_length)),
                    )
                )

        return tuple(options)

    @property
    def monitor_key(self) -> str:
        """Return a stable identifier for the date grid."""

        airports = ",".join(sorted(self.destination_airports))

        departure_days = ",".join(str(day) for day in sorted(self.departure_days))

        trip_lengths = ",".join(str(length) for length in sorted(self.trip_lengths))

        return "|".join(
            [
                "flexible-grid",
                self.origin,
                airports,
                f"{self.year:04d}-{self.month:02d}",
                f"days={departure_days}",
                f"stays={trip_lengths}",
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
