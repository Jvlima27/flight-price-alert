from flight_alert.models import (
    FlexibleDealResult,
    PriceResult,
    Route,
)


def convert_flexible_deal_to_price_result(
    deal: FlexibleDealResult,
) -> PriceResult:
    """Convert a flexible deal into the common monitoring model."""

    search = deal.search

    route = Route(
        origin=deal.origin,
        destination=deal.destination,
        departure_date=deal.departure_date,
        return_date=deal.return_date,
        target_price=search.target_price,
        direct_only=search.direct_only,
        minimum_alert_drop=search.minimum_alert_drop,
    )

    return PriceResult(
        route=route,
        price=deal.price,
        airline=deal.airline,
        source=deal.source,
        monitor_key=search.monitor_key,
        booking_url=deal.booking_url,
        checked_at=deal.checked_at,
    )
