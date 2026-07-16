from decimal import Decimal

from flight_alert.models import PriceResult, Route
from flight_alert.providers.base import FlightPriceProvider


class SimulatedFlightPriceProvider(FlightPriceProvider):
    """Provider that returns a fixed price for development and tests."""

    def __init__(
        self,
        price: Decimal | None = None,
        airline: str = "Simulated Air",
    ) -> None:
        self._price = price if price is not None else Decimal("2799.90")
        self._airline = airline

    @property
    def name(self) -> str:
        return "simulated"

    def search(self, route: Route) -> PriceResult:
        return PriceResult(
            route=route,
            price=self._price,
            airline=self._airline,
            source=self.name,
        )
