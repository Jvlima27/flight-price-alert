from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from flight_alert.insights import GeminiPriceInsightGenerator
from flight_alert.models import PriceResult, Route
from flight_alert.services import (
    analyze_price,
    analyze_price_history,
    decide_alert,
)


def test_generate_gemini_price_insight() -> None:
    route = Route(
        origin="VIX",
        destination="SCL",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 22),
        target_price=Decimal("2500.00"),
    )

    result = PriceResult(
        route=route,
        price=Decimal("2100.00"),
        airline="Test Air",
        source="test",
    )

    price_analysis = analyze_price(result)

    history_analysis = analyze_price_history(
        result=result,
        previous_price=Decimal("2300.00"),
        previous_lowest_price=Decimal("2200.00"),
    )

    decision = decide_alert(
        price_analysis=price_analysis,
        history_analysis=history_analysis,
        last_alerted_price=Decimal("2300.00"),
        minimum_alert_drop=Decimal("50.00"),
    )

    response = MagicMock()
    response.text = "O preço está abaixo da meta e representa um novo menor valor registrado."

    client = MagicMock()
    client.models.generate_content.return_value = response

    generator = GeminiPriceInsightGenerator(
        api_key="test-api-key",
        client=client,
    )

    insight = generator.generate(
        price_analysis=price_analysis,
        history_analysis=history_analysis,
        alert_decision=decision,
    )

    assert "abaixo da meta" in insight
    assert "novo menor valor" in insight

    client.models.generate_content.assert_called_once()
