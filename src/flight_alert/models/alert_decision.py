from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class AlertReason(StrEnum):
    """Reason for sending or suppressing an alert."""

    ABOVE_TARGET = "above_target"
    FIRST_TARGET_MATCH = "first_target_match"
    REENTERED_TARGET = "reentered_target"
    SIGNIFICANT_DROP = "significant_drop"
    DUPLICATE_OR_SMALL_DROP = "duplicate_or_small_drop"


@dataclass(frozen=True, slots=True)
class AlertDecision:
    """Decision about whether a notification should be sent."""

    should_notify: bool
    reason: AlertReason
    last_alerted_price: Decimal | None
    drop_since_last_alert: Decimal | None
