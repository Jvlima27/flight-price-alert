import logging
import os

from dotenv import load_dotenv

from flight_alert.config import ConfigurationError
from flight_alert.flexible_app import (
    FlexibleDealsApplication,
)
from flight_alert.main import (
    configure_logging,
    create_insight_generator,
    create_notifier,
)
from flight_alert.notifications import NotificationError
from flight_alert.providers import (
    ProviderError,
    SerpApiFlexibleGridProvider,
)


def main() -> None:
    configure_logging()
    load_dotenv()

    api_key = os.getenv(
        "SERPAPI_API_KEY",
        "",
    ).strip()

    if not api_key:
        logging.getLogger(__name__).error("SERPAPI_API_KEY is not configured.")
        raise SystemExit(1)

    try:
        FlexibleDealsApplication(
            provider=SerpApiFlexibleGridProvider(api_key=api_key),
            notifier=create_notifier(),
            insight_generator=create_insight_generator(),
        ).run()
    except (
        ConfigurationError,
        NotificationError,
        ProviderError,
    ) as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
