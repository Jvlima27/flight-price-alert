from decimal import Decimal

from flight_alert.models import (
    AlertDecision,
    AlertReason,
    PriceAnalysis,
    PriceHistoryAnalysis,
)


def decide_alert(
    price_analysis: PriceAnalysis,
    history_analysis: PriceHistoryAnalysis,
    last_alerted_price: Decimal | None,
    minimum_alert_drop: Decimal,
) -> AlertDecision:
    """Decide whether the current result deserves a notification."""

    current_price = price_analysis.result.price
    target_price = price_analysis.target_price

    if not price_analysis.should_alert:
        return AlertDecision(
            should_notify=False,
            reason=AlertReason.ABOVE_TARGET,
            last_alerted_price=last_alerted_price,
            drop_since_last_alert=None,
        )

    if last_alerted_price is None:
        return AlertDecision(
            should_notify=True,
            reason=AlertReason.FIRST_TARGET_MATCH,
            last_alerted_price=None,
            drop_since_last_alert=None,
        )

    previous_price = history_analysis.previous_price

    if (
        previous_price is not None
        and previous_price > target_price
        and current_price <= target_price
    ):
        return AlertDecision(
            should_notify=True,
            reason=AlertReason.REENTERED_TARGET,
            last_alerted_price=last_alerted_price,
            drop_since_last_alert=last_alerted_price - current_price,
        )

    drop_since_last_alert = last_alerted_price - current_price

    if drop_since_last_alert > Decimal("0") and drop_since_last_alert >= minimum_alert_drop:
        return AlertDecision(
            should_notify=True,
            reason=AlertReason.SIGNIFICANT_DROP,
            last_alerted_price=last_alerted_price,
            drop_since_last_alert=drop_since_last_alert,
        )

    return AlertDecision(
        should_notify=False,
        reason=AlertReason.DUPLICATE_OR_SMALL_DROP,
        last_alerted_price=last_alerted_price,
        drop_since_last_alert=drop_since_last_alert,
    )
