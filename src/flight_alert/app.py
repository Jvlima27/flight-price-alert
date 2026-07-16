import logging
from pathlib import Path

from flight_alert.config import load_routes
from flight_alert.providers import (
    FlightPriceProvider,
    SimulatedFlightPriceProvider,
)

logger = logging.getLogger(__name__)


class Application:
    """Main application class."""

    def __init__(
        self,
        routes_file: Path | None = None,
        provider: FlightPriceProvider | None = None,
    ) -> None:
        self.routes_file = routes_file or Path("config/routes.json")
        self.provider = provider or SimulatedFlightPriceProvider()

    def run(self) -> None:
        routes = load_routes(self.routes_file)

        logger.info("Loaded %d monitored route(s).", len(routes))
        logger.info("Using price provider: %s.", self.provider.name)

        for route in routes:
            logger.info(
                "Searching price for %s -> %s.",
                route.origin,
                route.destination,
            )

            result = self.provider.search(route)

            logger.info(
                "Price found: %s -> %s | airline=%s | price=R$ %s | source=%s",
                result.route.origin,
                result.route.destination,
                result.airline,
                f"{result.price:.2f}",
                result.source,
            )
