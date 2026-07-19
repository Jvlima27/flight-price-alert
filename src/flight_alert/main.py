import logging
import os

from dotenv import load_dotenv

from flight_alert.app import Application
from flight_alert.config import ConfigurationError
from flight_alert.insights import (
    GeminiPriceInsightGenerator,
    PriceInsightGenerator,
)
from flight_alert.notifications import (
    DiscordWebhookNotifier,
    NotificationError,
    PriceAlertNotifier,
)
from flight_alert.providers import (
    FlightPriceProvider,
    ProviderError,
    SerpApiFlightPriceProvider,
    SimulatedFlightPriceProvider,
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )


def create_provider() -> FlightPriceProvider:
    provider_name = (
        os.getenv(
            "FLIGHT_PROVIDER",
            "simulated",
        )
        .strip()
        .lower()
    )

    if provider_name == "simulated":
        return SimulatedFlightPriceProvider()

    if provider_name == "serpapi":
        api_key = os.getenv("SERPAPI_API_KEY", "").strip()

        if not api_key:
            raise ConfigurationError("SERPAPI_API_KEY is required when FLIGHT_PROVIDER=serpapi.")

        return SerpApiFlightPriceProvider(api_key=api_key)

    raise ConfigurationError(f"Unsupported FLIGHT_PROVIDER: '{provider_name}'.")


def create_notifier() -> PriceAlertNotifier | None:
    webhook_url = os.getenv(
        "DISCORD_WEBHOOK_URL",
        "",
    ).strip()

    if not webhook_url:
        logging.getLogger(__name__).warning(
            "DISCORD_WEBHOOK_URL is not configured. Discord alerts are disabled."
        )
        return None

    return DiscordWebhookNotifier(webhook_url=webhook_url)


def create_insight_generator() -> PriceInsightGenerator | None:
    enabled = os.getenv(
        "AI_INSIGHTS_ENABLED",
        "false",
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    if not enabled:
        return None

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise ConfigurationError("GEMINI_API_KEY is required when AI_INSIGHTS_ENABLED=true.")

    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.1-flash-lite",
    ).strip()

    return GeminiPriceInsightGenerator(
        api_key=api_key,
        model=model,
    )


def main() -> None:
    configure_logging()
    load_dotenv()

    try:
        Application(
            provider=create_provider(),
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
