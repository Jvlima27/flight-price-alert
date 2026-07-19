import logging
from pathlib import Path

from flight_alert.config import load_flexible_searches
from flight_alert.database import SQLitePriceRepository
from flight_alert.insights import PriceInsightGenerator
from flight_alert.notifications import PriceAlertNotifier
from flight_alert.providers import (
    FlexibleFlightDealsProvider,
    NoFlightResultsError,
)
from flight_alert.services import (
    PriceMonitoringEngine,
    convert_flexible_deal_to_price_result,
)

logger = logging.getLogger(__name__)


class FlexibleDealsApplication:
    """Application for flexible monthly flight searches."""

    def __init__(
        self,
        provider: FlexibleFlightDealsProvider,
        searches_file: Path | None = None,
        repository: SQLitePriceRepository | None = None,
        notifier: PriceAlertNotifier | None = None,
        insight_generator: PriceInsightGenerator | None = None,
        engine: PriceMonitoringEngine | None = None,
    ) -> None:
        self.provider = provider

        self.searches_file = searches_file or Path("config/flexible_routes.json")

        repository_instance = repository or SQLitePriceRepository(Path("data/flight_prices.db"))

        self.engine = engine or PriceMonitoringEngine(
            repository=repository_instance,
            notifier=notifier,
            insight_generator=insight_generator,
        )

    def run(self) -> None:
        self.engine.initialize()

        searches = load_flexible_searches(self.searches_file)

        logger.info(
            "Loaded %d flexible search(es).",
            len(searches),
        )

        logger.info(
            "Using flexible deals provider: %s.",
            self.provider.name,
        )

        for search in searches:
            logger.info(
                "Searching flexible deals: %s -> %s | %s to %s | %d-%d days.",
                search.origin,
                search.destination_name,
                search.outbound_start_date,
                search.outbound_end_date,
                search.minimum_trip_days,
                search.maximum_trip_days,
            )

            try:
                deal = self.provider.search(search)
            except NoFlightResultsError as exc:
                logger.warning(
                    "No matching flexible deal: %s",
                    exc,
                )
                continue

            logger.info(
                "Flexible deal selected: %s -> %s | departure=%s | return=%s | days=%d.",
                deal.origin,
                deal.destination,
                deal.departure_date,
                deal.return_date,
                deal.trip_days,
            )

            result = convert_flexible_deal_to_price_result(deal)

            self.engine.process(result)
