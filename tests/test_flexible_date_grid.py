from datetime import date
from decimal import Decimal

from flight_alert.models import FlexibleMonthSearch


def test_generate_rotating_date_grid() -> None:
    search = FlexibleMonthSearch(
        origin="VIX",
        destination_name="Buenos Aires",
        destination_airports=("AEP", "EZE"),
        year=2027,
        month=5,
        departure_days=(1, 6),
        trip_lengths=(5, 8),
        target_price=Decimal("2500.00"),
    )

    options = search.date_options

    assert len(options) == 4

    assert options[0].departure_date == date(
        2027,
        5,
        1,
    )
    assert options[0].return_date == date(
        2027,
        5,
        6,
    )

    assert options[1].return_date == date(
        2027,
        5,
        9,
    )

    assert options[2].departure_date == date(
        2027,
        5,
        6,
    )
    assert options[2].return_date == date(
        2027,
        5,
        11,
    )


def test_monitor_key_does_not_depend_on_found_dates() -> None:
    search = FlexibleMonthSearch(
        origin="VIX",
        destination_name="Buenos Aires",
        destination_airports=("EZE", "AEP"),
        year=2027,
        month=5,
        departure_days=(11, 1, 6),
        trip_lengths=(12, 5, 8),
        target_price=Decimal("2500.00"),
    )

    assert search.monitor_key == ("flexible-grid|VIX|AEP,EZE|2027-05|days=1,6,11|stays=5,8,12|0")
