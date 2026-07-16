from datetime import date
from decimal import Decimal

import pytest

from flight_alert.models import PriceResult, Route


def test_reject_non_positive_price_result() -> None:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        target_price=Decimal("2500.00"),
    )

    with pytest.raises(
        ValueError,
        match="Price must be greater than zero",
    ):
        PriceResult(
            route=route,
            price=Decimal("0"),
            airline="Test Air",
            source="test",
        )
