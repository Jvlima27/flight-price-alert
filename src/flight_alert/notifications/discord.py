import json
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flight_alert.models import PriceAnalysis, PriceHistoryAnalysis
from flight_alert.notifications.base import PriceAlertNotifier


class NotificationError(RuntimeError):
    """Raised when a notification cannot be delivered."""


class DiscordWebhookNotifier(PriceAlertNotifier):
    """Send flight price alerts through a Discord webhook."""

    def __init__(
        self,
        webhook_url: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        if not webhook_url.strip():
            raise ValueError("Discord webhook URL cannot be empty.")

        self.webhook_url = webhook_url.strip()
        self.timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "discord"

    def send(
        self,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
    ) -> None:
        payload = self._build_payload(
            price_analysis=price_analysis,
            history_analysis=history_analysis,
        )

        request = Request(
            url=self.webhook_url,
            data=json.dumps(
                payload,
                ensure_ascii=False,
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "flight-price-alert/0.1.0",
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                if not 200 <= response.status < 300:
                    raise NotificationError(
                        f"Discord returned an unsuccessful response: HTTP {response.status}."
                    )
        except HTTPError as exc:
            raise NotificationError(
                f"Discord rejected the notification with HTTP {exc.code}."
            ) from exc
        except URLError as exc:
            raise NotificationError("Could not connect to the Discord webhook.") from exc

    @staticmethod
    def _build_payload(
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
    ) -> dict[str, object]:
        result = price_analysis.result
        route = result.route

        description = (
            "Encontramos uma passagem dentro da meta configurada "
            f"de {_format_brl(route.target_price)}."
        )

        if history_analysis.is_new_lowest:
            description += "\n\n🏆 Este é um novo menor preço registrado."

        departure = route.departure_date.strftime("%d/%m/%Y")
        return_date = (
            route.return_date.strftime("%d/%m/%Y")
            if route.return_date is not None
            else "Somente ida"
        )

        embed: dict[str, object] = {
            "title": "✈️ Passagem dentro da meta!",
            "description": description,
            "color": 5763719,
            "fields": [
                {
                    "name": "Rota",
                    "value": f"{route.origin} → {route.destination}",
                    "inline": True,
                },
                {
                    "name": "Datas",
                    "value": f"{departure} → {return_date}",
                    "inline": True,
                },
                {
                    "name": "Preço encontrado",
                    "value": _format_brl(result.price),
                    "inline": True,
                },
                {
                    "name": "Economia sobre a meta",
                    "value": _format_brl(price_analysis.difference),
                    "inline": True,
                },
                {
                    "name": "Companhia",
                    "value": result.airline,
                    "inline": True,
                },
                {
                    "name": "Variação",
                    "value": _format_history_change(history_analysis),
                    "inline": True,
                },
            ],
            "footer": {
                "text": f"Fonte: {result.source}",
            },
            "timestamp": result.checked_at.isoformat(),
        }

        if result.booking_url is not None:
            embed["url"] = result.booking_url

        return {
            "username": "Flight Price Alert",
            "allowed_mentions": {
                "parse": [],
            },
            "embeds": [embed],
        }


def _format_brl(value: Decimal) -> str:
    formatted = f"{value:,.2f}"

    formatted = formatted.replace(",", "_").replace(".", ",").replace("_", ".")

    return f"R$ {formatted}"


def _format_percentage(value: Decimal) -> str:
    return f"{abs(value):.2f}".replace(".", ",") + "%"


def _format_history_change(
    analysis: PriceHistoryAnalysis,
) -> str:
    if analysis.change_amount is None or analysis.change_percentage is None:
        return "Primeiro preço registrado"

    if analysis.change_amount < 0:
        return (
            f"Queda de {_format_brl(abs(analysis.change_amount))} "
            f"({_format_percentage(analysis.change_percentage)})"
        )

    if analysis.change_amount > 0:
        return (
            f"Aumento de {_format_brl(analysis.change_amount)} "
            f"({_format_percentage(analysis.change_percentage)})"
        )

    return "Sem alteração"
