import logging
import os

from dotenv import load_dotenv

from flight_alert.config import ConfigurationError
from flight_alert.flexible_app import (
    FlexibleDealsApplication,
)
from flight_alert.providers import (
    ProviderError,
    SerpApiFlexibleDealsProvider,
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
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
        FlexibleDealsApplication(provider=SerpApiFlexibleDealsProvider(api_key=api_key)).run()
    except (ConfigurationError, ProviderError) as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
