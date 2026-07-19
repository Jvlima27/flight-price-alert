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
        month=5,
        departure_days=(1, 6, 11),
        trip_lengths=(5, 8, 12),
        target_price=Decimal("2500.00"),
    )

    deal = FlexibleDealResult(
        search=search,
        price=Decimal("1800.00"),
        origin="VIX",
        destination="AEP",
        departure_date=date(2027, 5, 6),
        return_date=date(2027, 5, 14),
        airline="Test Air",
        source="test",
    )

    result = convert_flexible_deal_to_price_result(deal)

    assert result.monitor_key == search.monitor_key
    assert result.route.departure_date == date(
        2027,
        5,
        6,
    )
    assert result.route.return_date == date(
        2027,
        5,
        14,
    )
    assert result.route.target_price == Decimal("2500.00")
