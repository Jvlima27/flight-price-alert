import logging
from pathlib import Path

from flight_alert.config import load_routes
from flight_alert.database import SQLitePriceRepository
from flight_alert.models import (
    PriceAnalysis,
    PriceHistoryAnalysis,
    PriceStatus,
)
from flight_alert.notifications import PriceAlertNotifier
from flight_alert.providers import (
    FlightPriceProvider,
    SimulatedFlightPriceProvider,
)
from flight_alert.services import analyze_price, analyze_price_history

logger = logging.getLogger(__name__)


class Application:
    """Main application class."""

    def __init__(
        self,
        routes_file: Path | None = None,
        provider: FlightPriceProvider | None = None,
        repository: SQLitePriceRepository | None = None,
        notifier: PriceAlertNotifier | None = None,
    ) -> None:
        self.routes_file = routes_file or Path("config/routes.json")
        self.provider = provider or SimulatedFlightPriceProvider()
        self.repository = repository or SQLitePriceRepository(Path("data/flight_prices.db"))
        self.notifier = notifier

    def run(self) -> None:
        self.repository.initialize()

        routes = load_routes(self.routes_file)

        logger.info("Loaded %d monitored route(s).", len(routes))
        logger.info("Using price provider: %s.", self.provider.name)

        for route in routes:
            logger.info(
                "Searching price for %s -> %s.",
                route.origin,
                route.destination,
            )

            previous_price = self.repository.get_latest_price(route)
            previous_lowest_price = self.repository.get_lowest_price(route)

            result = self.provider.search(route)

            price_analysis = analyze_price(result)
            history_analysis = analyze_price_history(
                result=result,
                previous_price=previous_price,
                previous_lowest_price=previous_lowest_price,
            )

            self.repository.save(result)

            self._log_price_analysis(price_analysis)
            self._log_history_analysis(history_analysis)
            self._send_alert_if_required(
                price_analysis=price_analysis,
                history_analysis=history_analysis,
            )

    def _send_alert_if_required(
        self,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
    ) -> None:
        if not price_analysis.should_alert:
            return

        if self.notifier is None:
            logger.warning("The alert condition was met, but no notifier is configured.")
            return

        self.notifier.send(
            price_analysis=price_analysis,
            history_analysis=history_analysis,
        )

        logger.info("Price alert sent successfully.")

    @staticmethod
    def _log_price_analysis(analysis: PriceAnalysis) -> None:
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
                "Price is R$ %s above the target (%s%%). No target alert required.",
                f"{abs(analysis.difference):.2f}",
                f"{abs(analysis.difference_percentage):.2f}",
            )
            return

        logger.info(
            "Price reached the target. Savings: R$ %s (%s%%). Target alert required.",
            f"{analysis.difference:.2f}",
            f"{analysis.difference_percentage:.2f}",
        )

    @staticmethod
    def _log_history_analysis(
        analysis: PriceHistoryAnalysis,
    ) -> None:
        if analysis.previous_price is None:
            logger.info("This is the first recorded price for this route.")
        elif analysis.change_amount is None:
            logger.info("Historical price variation is unavailable.")
        elif analysis.change_amount < 0:
            logger.info(
                "Price dropped by R$ %s (%s%%) since the previous check.",
                f"{abs(analysis.change_amount):.2f}",
                f"{abs(analysis.change_percentage):.2f}",
            )
        elif analysis.change_amount > 0:
            logger.info(
                "Price increased by R$ %s (%s%%) since the previous check.",
                f"{analysis.change_amount:.2f}",
                f"{analysis.change_percentage:.2f}",
            )
        else:
            logger.info("Price has not changed since the previous check.")

        if analysis.is_new_lowest:
            logger.info("This is a new lowest recorded price.")
