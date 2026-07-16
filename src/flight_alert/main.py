import logging

from flight_alert.app import Application
from flight_alert.config import ConfigurationError


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )


def main() -> None:
    configure_logging()

    try:
        Application().run()
    except ConfigurationError as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
