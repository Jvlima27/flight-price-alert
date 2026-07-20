import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from flight_alert.models import PriceResult, Route
from flight_alert.notifications import DiscordWebhookNotifier
from flight_alert.services import analyze_price, analyze_price_history


@patch("flight_alert.notifications.discord.urlopen")
def test_send_discord_price_alert(
    mocked_urlopen: MagicMock,
) -> None:
    response = MagicMock()
    response.status = 204

    mocked_urlopen.return_value.__enter__.return_value = response

    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal("2500.00"),
    )

    result = PriceResult(
        route=route,
        price=Decimal("2199.90"),
        airline="Test Air",
        source="test",
    )

    price_analysis = analyze_price(result)

    history_analysis = analyze_price_history(
        result=result,
        previous_price=Decimal("2300.00"),
        previous_lowest_price=Decimal("2250.00"),
    )

    notifier = DiscordWebhookNotifier(
        webhook_url=("https://discord.com/api/webhooks/123456789/test-token")
    )

    notifier.send(
        price_analysis=price_analysis,
        history_analysis=history_analysis,
    )

    mocked_urlopen.assert_called_once()

    request = mocked_urlopen.call_args.args[0]
    payload = json.loads(request.data.decode("utf-8"))

    embed = payload["embeds"][0]
    field_values = [field["value"] for field in embed["fields"]]

    assert embed["title"] == "✈️ Passagem dentro da meta!"
    assert "VIX → SCL" in field_values
    assert "R$ 2.199,90" in field_values
    assert "Test Air" in field_values


def test_build_flexible_discord_payload() -> None:
    route = Route(
        origin="VIX",
        destination="EZE",
        departure_date=date(2027, 6, 1),
        return_date=date(2027, 6, 9),
        target_price=Decimal("2500.00"),
    )

    result = PriceResult(
        route=route,
        price=Decimal("2297.00"),
        airline="Gol",
        source=("serpapi_google_flights_flexible_grid"),
        monitor_key=("flexible-grid|VIX|AEP,EZE|2027-06|days=1,6,11|stays=5,8,12|0"),
    )

    price_analysis = analyze_price(result)

    history_analysis = analyze_price_history(
        result=result,
        previous_price=None,
        previous_lowest_price=None,
    )

    payload = DiscordWebhookNotifier._build_payload(
        price_analysis=price_analysis,
        history_analysis=history_analysis,
    )

    embed = payload["embeds"][0]

    assert embed["title"] == "🔎 Oferta flexível dentro da meta!"

    fields = {field["name"]: field["value"] for field in embed["fields"]}

    assert fields["Tipo de busca"] == "Grade flexível rotativa"

    assert fields["Duração"] == "8 dias"
    assert fields["Preço encontrado"] == "R$ 2.297,00"
