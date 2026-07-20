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
        insight: str | None = None,
    ) -> None:
        payload = self._build_payload(
            price_analysis=price_analysis,
            history_analysis=history_analysis,
            insight=insight,
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
        insight: str | None = None,
    ) -> dict[str, object]:
        result = price_analysis.result
        route = result.route

        is_flexible = _is_flexible_monitor(result.monitor_key)

        if is_flexible:
            title = "🔎 Oferta flexível dentro da meta!"

            description = (
                "Encontramos uma combinação de datas da "
                "grade flexível dentro da meta configurada "
                f"de {_format_brl(route.target_price)}."
            )

            color = 3447003
        else:
            title = "✈️ Passagem dentro da meta!"

            description = (
                "Encontramos uma passagem dentro da "
                "meta configurada "
                f"de {_format_brl(route.target_price)}."
            )

            color = 5763719

        if history_analysis.is_new_lowest:
            description += "\n\n🏆 Este é um novo menor preço registrado."

        departure = route.departure_date.strftime("%d/%m/%Y")

        return_date = (
            route.return_date.strftime("%d/%m/%Y")
            if route.return_date is not None
            else "Somente ida"
        )

        trip_duration = (
            (route.return_date - route.departure_date).days
            if route.return_date is not None
            else None
        )

        search_type = "Grade flexível rotativa" if is_flexible else "Datas exatas"

        duration_text = f"{trip_duration} dias" if trip_duration is not None else "Somente ida"

        fields: list[dict[str, object]] = [
            {
                "name": "Rota",
                "value": (f"{route.origin} → {route.destination}"),
                "inline": True,
            },
            {
                "name": "Tipo de busca",
                "value": search_type,
                "inline": True,
            },
            {
                "name": "Datas",
                "value": (f"{departure} → {return_date}"),
                "inline": True,
            },
            {
                "name": "Duração",
                "value": duration_text,
                "inline": True,
            },
            {
                "name": "Preço encontrado",
                "value": _format_brl(result.price),
                "inline": True,
            },
            {
                "name": "Meta configurada",
                "value": _format_brl(route.target_price),
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
        ]

        if insight:
            fields.append(
                {
                    "name": "🤖 Análise da IA",
                    "value": insight[:1024],
                    "inline": False,
                }
            )

        footer_text = f"Fonte: {result.source}"

        if is_flexible:
            footer_text += " • Scanner rotativo"

        embed: dict[str, object] = {
            "title": title,
            "description": description,
            "color": color,
            "fields": fields,
            "footer": {
                "text": footer_text,
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


def _is_flexible_monitor(
    monitor_key: str | None,
) -> bool:
    if monitor_key is None:
        return False

    return monitor_key.startswith("flexible-grid|")


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
