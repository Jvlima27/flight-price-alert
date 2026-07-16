from datetime import date
from decimal import Decimal

from flight_alert.models import PriceResult, PriceStatus, Route
from flight_alert.services import analyze_price


def create_result(price: str, target_price: str = "2500.00") -> PriceResult:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal(target_price),
    )

    return PriceResult(
        route=route,
        price=Decimal(price),
        airline="Test Air",
        source="test",
    )


def test_price_below_target_should_generate_alert() -> None:
    result = create_result("2000.00")

    analysis = analyze_price(result)

    assert analysis.status is PriceStatus.BELOW_TARGET
    assert analysis.difference == Decimal("500.00")
    assert analysis.difference_percentage == Decimal("20.00")
    assert analysis.should_alert is True


def test_price_equal_to_target_should_generate_alert() -> None:
    result = create_result("2500.00")

    analysis = analyze_price(result)

    assert analysis.status is PriceStatus.AT_TARGET
    assert analysis.difference == Decimal("0.00")
    assert analysis.difference_percentage == Decimal("0.00")
    assert analysis.should_alert is True


def test_price_above_target_should_not_generate_alert() -> None:
    result = create_result("3000.00")

    analysis = analyze_price(result)

    assert analysis.status is PriceStatus.ABOVE_TARGET
    assert analysis.difference == Decimal("-500.00")
    assert analysis.difference_percentage == Decimal("-20.00")
    assert analysis.should_alert is False
