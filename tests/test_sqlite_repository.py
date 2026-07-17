from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from flight_alert.database import SQLitePriceRepository
from flight_alert.models import PriceResult, Route


def create_route() -> Route:
    return Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal("2500.00"),
    )


def create_result(
    route: Route,
    price: str,
    checked_at: datetime,
) -> PriceResult:
    return PriceResult(
        route=route,
        price=Decimal(price),
        airline="Test Air",
        source="test",
        checked_at=checked_at,
    )


def test_save_and_retrieve_price_history(tmp_path: Path) -> None:
    repository = SQLitePriceRepository(tmp_path / "prices.db")
    repository.initialize()

    route = create_route()

    first_result = create_result(
        route=route,
        price="2300.00",
        checked_at=datetime(2026, 7, 16, 10, 0, tzinfo=timezone.utc),
    )

    second_result = create_result(
        route=route,
        price="2100.00",
        checked_at=datetime(2026, 7, 16, 11, 0, tzinfo=timezone.utc),
    )

    repository.save(first_result)
    repository.save(second_result)

    assert repository.count(route) == 2
    assert repository.get_latest_price(route) == Decimal("2100.00")
    assert repository.get_lowest_price(route) == Decimal("2100.00")
