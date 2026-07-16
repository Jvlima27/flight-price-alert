import logging
from pathlib import Path

from flight_alert.config import load_routes

logger = logging.getLogger(__name__)


class Application:
    """Main application class."""

    def __init__(self, routes_file: Path | None = None) -> None:
        self.routes_file = routes_file or Path("config/routes.json")

    def run(self) -> None:
        routes = load_routes(self.routes_file)

        logger.info("Loaded %d monitored route(s).", len(routes))

        for route in routes:
            target_price = f"{route.target_price:.2f}"
            return_date = route.return_date or "-"

            logger.info(
                "%s -> %s | departure=%s | return=%s | target=R$ %s | direct_only=%s",
                route.origin,
                route.destination,
                route.departure_date,
                return_date,
                target_price,
                route.direct_only,
            )
