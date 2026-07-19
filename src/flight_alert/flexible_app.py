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
    """Application for rotating flexible date searches."""

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

        self.repository = repository or SQLitePriceRepository(Path("data/flight_prices.db"))

        self.engine = engine or PriceMonitoringEngine(
            repository=self.repository,
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
            "Using flexible provider: %s.",
            self.provider.name,
        )

        for search in searches:
            options = search.date_options
            option_count = len(options)

            cursor_position = self.repository.get_cursor_position(
                monitor_key=search.monitor_key,
                option_count=option_count,
            )

            date_option = options[cursor_position]

            logger.info(
                "Flexible grid option %d/%d: %s -> %s | departure=%s | return=%s | days=%d.",
                cursor_position + 1,
                option_count,
                search.origin,
                search.destination_name,
                date_option.departure_date,
                date_option.return_date,
                date_option.trip_days,
            )

            try:
                deal = self.provider.search(
                    search=search,
                    date_option=date_option,
                )
            except NoFlightResultsError as exc:
                next_position = self.repository.advance_cursor(
                    monitor_key=search.monitor_key,
                    option_count=option_count,
                )

                logger.warning(
                    "No results for this date combination: %s",
                    exc,
                )

                logger.info(
                    "Flexible cursor advanced to option %d/%d.",
                    next_position + 1,
                    option_count,
                )

                continue

            next_position = self.repository.advance_cursor(
                monitor_key=search.monitor_key,
                option_count=option_count,
            )

            logger.info(
                "Flexible deal selected: %s -> %s | departure=%s | return=%s | days=%d.",
                deal.origin,
                deal.destination,
                deal.departure_date,
                deal.return_date,
                deal.trip_days,
            )

            logger.info(
                "Flexible cursor advanced to option %d/%d.",
                next_position + 1,
                option_count,
            )

            result = convert_flexible_deal_to_price_result(deal)

            self.engine.process(result)
