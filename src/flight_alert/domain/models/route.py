from dataclasses import dataclass
from datetime import date


@dataclass(slots=True, frozen=True)
class Route:
    origin: str
    destination: str
    departure_date: date
    return_date: date | None
    target_price: float