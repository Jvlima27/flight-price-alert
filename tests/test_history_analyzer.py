from datetime import date
from decimal import Decimal

from flight_alert.models import PriceResult, Route
from flight_alert.services import analyze_price_history


def create_result(price: str) -> PriceResult:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        target_price=Decimal("2500.00"),
    )

    return PriceResult(
        route=route,
        price=Decimal(price),
        airline="Test Air",
        source="test",
    )


def test_first_price_is_new_lowest() -> None:
    result = create_result("2200.00")

    analysis = analyze_price_history(
        result=result,
        previous_price=None,
        previous_lowest_price=None,
    )

    assert analysis.previous_price is None
    assert analysis.change_amount is None
    assert analysis.change_percentage is None
    assert analysis.is_new_lowest is True


def test_detect_price_drop_and_new_lowest() -> None:
    result = create_result("2000.00")

    analysis = analyze_price_history(
        result=result,
        previous_price=Decimal("2200.00"),
        previous_lowest_price=Decimal("2100.00"),
    )

    assert analysis.change_amount == Decimal("-200.00")
    assert analysis.change_percentage == Decimal("-9.09")
    assert analysis.is_new_lowest is True


def test_detect_price_increase() -> None:
    result = create_result("2400.00")

    analysis = analyze_price_history(
        result=result,
        previous_price=Decimal("2200.00"),
        previous_lowest_price=Decimal("2000.00"),
    )

    assert analysis.change_amount == Decimal("200.00")
    assert analysis.change_percentage == Decimal("9.09")
    assert analysis.is_new_lowest is False
