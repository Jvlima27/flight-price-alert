from decimal import Decimal, ROUND_HALF_UP

from flight_alert.models import PriceAnalysis, PriceResult, PriceStatus

PERCENTAGE_PRECISION = Decimal("0.01")


def analyze_price(result: PriceResult) -> PriceAnalysis:
    """Compare a price result with the configured target price."""

    target_price = result.route.target_price
    difference = target_price - result.price

    difference_percentage = (difference / target_price * Decimal("100")).quantize(
        PERCENTAGE_PRECISION,
        rounding=ROUND_HALF_UP,
    )

    if result.price < target_price:
        status = PriceStatus.BELOW_TARGET
    elif result.price == target_price:
        status = PriceStatus.AT_TARGET
    else:
        status = PriceStatus.ABOVE_TARGET

    return PriceAnalysis(
        result=result,
        status=status,
        difference=difference,
        difference_percentage=difference_percentage,
        should_alert=result.price <= target_price,
    )
