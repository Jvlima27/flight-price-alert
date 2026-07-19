from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class FlexibleDateOption:
    """One departure and return date combination."""

    departure_date: date
    return_date: date

    def __post_init__(self) -> None:
        if self.return_date <= self.departure_date:
            raise ValueError("Return date must be after departure date.")

    @property
    def trip_days(self) -> int:
        return (self.return_date - self.departure_date).days
