import logging
from pathlib import Path

from flight_alert.config import load_routes
from flight_alert.models import PriceAnalysis, PriceStatus
from flight_alert.providers import (
    FlightPriceProvider,
    SimulatedFlightPriceProvider,
)
from flight_alert.services import analyze_price

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
            analysis = analyze_price(result)

            self._log_analysis(analysis)

    @staticmethod
    def _log_analysis(analysis: PriceAnalysis) -> None:
        result = analysis.result
        route = result.route

        logger.info(
            "Price found: %s -> %s | airline=%s | price=R$ %s | target=R$ %s | source=%s",
            route.origin,
            route.destination,
            result.airline,
            f"{result.price:.2f}",
            f"{route.target_price:.2f}",
            result.source,
        )

        if analysis.status is PriceStatus.ABOVE_TARGET:
            logger.info(
                "Price is R$ %s above the target (%s%%). No alert required.",
                f"{abs(analysis.difference):.2f}",
                f"{abs(analysis.difference_percentage):.2f}",
            )
            return

        logger.info(
            "Price reached the target. Savings: R$ %s (%s%%). Alert required.",
            f"{analysis.difference:.2f}",
            f"{analysis.difference_percentage:.2f}",
        )
