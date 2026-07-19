import logging
from pathlib import Path

from flight_alert.config import load_flexible_searches
from flight_alert.providers import (
    FlexibleFlightDealsProvider,
    NoFlightResultsError,
)

logger = logging.getLogger(__name__)


class FlexibleDealsApplication:
    """Application for flexible monthly flight searches."""

    def __init__(
        self,
        provider: FlexibleFlightDealsProvider,
        searches_file: Path | None = None,
    ) -> None:
        self.provider = provider
        self.searches_file = searches_file or Path("config/flexible_routes.json")

    def run(self) -> None:
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
                result = self.provider.search(search)
            except NoFlightResultsError as exc:
                logger.warning(
                    "No matching flexible deal: %s",
                    exc,
                )
                continue

            logger.info(
                "Cheapest flexible deal: %s -> %s | "
                "departure=%s | return=%s | days=%d | "
                "airline=%s | price=R$ %.2f | target=R$ %.2f",
                result.origin,
                result.destination,
                result.departure_date,
                result.return_date,
                result.trip_days,
                result.airline,
                result.price,
                search.target_price,
            )

            if result.price <= search.target_price:
                logger.info("Flexible deal reached the configured target.")
            else:
                logger.info(
                    "Flexible deal is R$ %.2f above the target.",
                    result.price - search.target_price,
                )
