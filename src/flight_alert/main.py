import logging
import os

from dotenv import load_dotenv

from flight_alert.app import Application
from flight_alert.config import ConfigurationError
from flight_alert.notifications import (
    DiscordWebhookNotifier,
    NotificationError,
    PriceAlertNotifier,
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )


def create_notifier() -> PriceAlertNotifier | None:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        logging.getLogger(__name__).warning(
            "DISCORD_WEBHOOK_URL is not configured. Discord alerts are disabled."
        )
        return None

    return DiscordWebhookNotifier(webhook_url=webhook_url)


def main() -> None:
    configure_logging()
    load_dotenv()

    try:
        Application(notifier=create_notifier()).run()
    except (ConfigurationError, NotificationError) as exc:
        logging.getLogger(__name__).error("%s", exc)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
