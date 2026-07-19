from pathlib import Path

from flight_alert.database import SQLitePriceRepository


def test_rotate_monitor_cursor(tmp_path: Path) -> None:
    repository = SQLitePriceRepository(tmp_path / "prices.db")

    repository.initialize()

    monitor_key = "flexible-grid-test"

    assert (
        repository.get_cursor_position(
            monitor_key=monitor_key,
            option_count=3,
        )
        == 0
    )

    repository.advance_cursor(
        monitor_key=monitor_key,
        option_count=3,
    )

    assert (
        repository.get_cursor_position(
            monitor_key=monitor_key,
            option_count=3,
        )
        == 1
    )

    repository.advance_cursor(
        monitor_key=monitor_key,
        option_count=3,
    )

    assert (
        repository.get_cursor_position(
            monitor_key=monitor_key,
            option_count=3,
        )
        == 2
    )

    repository.advance_cursor(
        monitor_key=monitor_key,
        option_count=3,
    )

    assert (
        repository.get_cursor_position(
            monitor_key=monitor_key,
            option_count=3,
        )
        == 0
    )
