from decimal import Decimal, ROUND_HALF_UP

from flight_alert.models import PriceHistoryAnalysis, PriceResult

PERCENTAGE_PRECISION = Decimal("0.01")


def analyze_price_history(
    result: PriceResult,
    previous_price: Decimal | None,
    previous_lowest_price: Decimal | None,
) -> PriceHistoryAnalysis:
    """Compare the current price with the recorded history."""

    change_amount: Decimal | None = None
    change_percentage: Decimal | None = None

    if previous_price is not None:
        change_amount = result.price - previous_price

        change_percentage = (change_amount / previous_price * Decimal("100")).quantize(
            PERCENTAGE_PRECISION,
            rounding=ROUND_HALF_UP,
        )

    is_new_lowest = previous_lowest_price is None or result.price < previous_lowest_price

    return PriceHistoryAnalysis(
        result=result,
        previous_price=previous_price,
        previous_lowest_price=previous_lowest_price,
        change_amount=change_amount,
        change_percentage=change_percentage,
        is_new_lowest=is_new_lowest,
    )
