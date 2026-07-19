from datetime import date
from decimal import Decimal

from flight_alert.models import (
    FlexibleDealResult,
    FlexibleMonthSearch,
)
from flight_alert.services import (
    convert_flexible_deal_to_price_result,
)


def test_flexible_deal_uses_stable_monitor_key() -> None:
    search = FlexibleMonthSearch(
        origin="VIX",
        destination_name="Buenos Aires",
        destination_airports=("AEP", "EZE"),
        year=2027,
        month=6,
        minimum_trip_days=5,
        maximum_trip_days=15,
        target_price=Decimal("2500.00"),
    )

    deal = FlexibleDealResult(
        search=search,
        price=Decimal("1800.00"),
        origin="VIX",
        destination="AEP",
        departure_date=date(2027, 6, 8),
        return_date=date(2027, 6, 15),
        airline="Test Air",
        source="test",
    )

    result = convert_flexible_deal_to_price_result(deal)

    assert result.monitor_key == ("flexible-month|VIX|AEP,EZE|2027-06|5-15|0")

    assert result.route.departure_date == date(
        2027,
        6,
        8,
    )

    assert result.route.return_date == date(
        2027,
        6,
        15,
    )

    assert result.route.target_price == Decimal("2500.00")
