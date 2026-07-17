import json
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from flight_alert.models import Route
from flight_alert.providers import SerpApiFlightPriceProvider


@patch("flight_alert.providers.serpapi.urlopen")
def test_serpapi_provider_returns_cheapest_offer(
    mocked_urlopen: MagicMock,
) -> None:
    payload = {
        "search_metadata": {"google_flights_url": ("https://www.google.com/travel/flights")},
        "best_flights": [
            {
                "price": 2199,
                "flights": [
                    {
                        "airline": "LATAM",
                    }
                ],
            }
        ],
        "other_flights": [
            {
                "price": 1899,
                "flights": [
                    {
                        "airline": "Sky Airline",
                    },
                    {
                        "airline": "LATAM",
                    },
                ],
            }
        ],
    }

    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")

    mocked_urlopen.return_value.__enter__.return_value = response

    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal("2500.00"),
        direct_only=True,
    )

    provider = SerpApiFlightPriceProvider(
        api_key="test-api-key",
    )

    result = provider.search(route)

    assert result.price == Decimal("1899")
    assert result.airline == "Sky Airline + LATAM"
    assert result.source == "serpapi_google_flights"
    assert result.booking_url == ("https://www.google.com/travel/flights")

    request = mocked_urlopen.call_args.args[0]
    parameters = parse_qs(urlparse(request.full_url).query)

    assert parameters["departure_id"] == ["VIX"]
    assert parameters["arrival_id"] == ["SCL"]
    assert parameters["currency"] == ["BRL"]
    assert parameters["type"] == ["1"]
    assert parameters["stops"] == ["1"]
