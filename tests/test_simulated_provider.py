from datetime import date
from decimal import Decimal

from flight_alert.models import Route
from flight_alert.providers import SimulatedFlightPriceProvider


def test_simulated_provider_returns_configured_price() -> None:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal("2500.00"),
    )

    provider = SimulatedFlightPriceProvider(
        price=Decimal("1999.90"),
        airline="Test Air",
    )

    result = provider.search(route)

    assert result.route == route
    assert result.price == Decimal("1999.90")
    assert result.airline == "Test Air"
    assert result.source == "simulated"
    assert result.checked_at.tzinfo is not None
