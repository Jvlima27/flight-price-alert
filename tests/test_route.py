from datetime import date
from decimal import Decimal

import pytest

from flight_alert.models import Route


def test_create_valid_route() -> None:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal("2500.00"),
    )

    assert route.origin == "VIX"
    assert route.destination == "SCL"
    assert route.target_price == Decimal("2500.00")


def test_reject_same_origin_and_destination() -> None:
    with pytest.raises(
        ValueError,
        match="Origin and destination must be different",
    ):
        Route(
            origin="VIX",
            destination="VIX",
            departure_date=date(2026, 10, 15),
            target_price=Decimal("500.00"),
        )


def test_reject_return_before_departure() -> None:
    with pytest.raises(
        ValueError,
        match="Return date cannot be before departure date",
    ):
        Route(
            origin="VIX",
            destination="SCL",
            departure_date=date(2026, 10, 15),
            return_date=date(2026, 10, 10),
            target_price=Decimal("2500.00"),
        )
