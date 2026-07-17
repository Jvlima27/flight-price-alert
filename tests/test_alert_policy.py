from datetime import date
from decimal import Decimal

from flight_alert.models import AlertDecision, PriceResult, Route
from flight_alert.services import (
    analyze_price,
    analyze_price_history,
    decide_alert,
)


def create_decision(
    current_price: str,
    previous_price: str | None,
    last_alerted_price: str | None,
    minimum_drop: str = "50.00",
) -> AlertDecision:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        target_price=Decimal("2500.00"),
        minimum_alert_drop=Decimal(minimum_drop),
    )

    result = PriceResult(
        route=route,
        price=Decimal(current_price),
        airline="Test Air",
        source="test",
    )

    price_analysis = analyze_price(result)

    history_analysis = analyze_price_history(
        result=result,
        previous_price=(Decimal(previous_price) if previous_price is not None else None),
        previous_lowest_price=None,
    )

    return decide_alert(
        price_analysis=price_analysis,
        history_analysis=history_analysis,
        last_alerted_price=(
            Decimal(last_alerted_price) if last_alerted_price is not None else None
        ),
        minimum_alert_drop=route.minimum_alert_drop,
    )


def test_first_target_match_should_notify() -> None:
    decision = create_decision(
        current_price="2200.00",
        previous_price=None,
        last_alerted_price=None,
    )

    assert decision.should_notify is True


def test_same_price_should_not_notify_again() -> None:
    decision = create_decision(
        current_price="2200.00",
        previous_price="2200.00",
        last_alerted_price="2200.00",
    )

    assert decision.should_notify is False


def test_significant_drop_should_notify() -> None:
    decision = create_decision(
        current_price="2100.00",
        previous_price="2200.00",
        last_alerted_price="2200.00",
        minimum_drop="50.00",
    )

    assert decision.should_notify is True
    assert decision.drop_since_last_alert == Decimal("100.00")


def test_small_drop_should_not_notify() -> None:
    decision = create_decision(
        current_price="2175.00",
        previous_price="2200.00",
        last_alerted_price="2200.00",
        minimum_drop="50.00",
    )

    assert decision.should_notify is False


def test_reentering_target_should_notify() -> None:
    decision = create_decision(
        current_price="2400.00",
        previous_price="2700.00",
        last_alerted_price="2300.00",
    )

    assert decision.should_notify is True
