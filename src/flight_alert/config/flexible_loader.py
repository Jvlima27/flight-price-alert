import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from flight_alert.config.loader import ConfigurationError
from flight_alert.models import FlexibleMonthSearch


def load_flexible_searches(
    file_path: Path,
) -> list[FlexibleMonthSearch]:
    """Load rotating flexible searches from a JSON file."""

    try:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Flexible configuration file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON in {file_path} at line {exc.lineno}, column {exc.colno}."
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError("The flexible configuration root must be an object.")

    raw_searches = data.get("searches")

    if not isinstance(raw_searches, list) or not raw_searches:
        raise ConfigurationError(
            "The flexible configuration must contain a non-empty 'searches' list."
        )

    return [
        _parse_flexible_search(raw_search, index)
        for index, raw_search in enumerate(
            raw_searches,
            start=1,
        )
    ]


def _parse_flexible_search(
    raw_search: Any,
    index: int,
) -> FlexibleMonthSearch:
    if not isinstance(raw_search, dict):
        raise ConfigurationError(f"Flexible search {index} must be an object.")

    try:
        destination_airports = _parse_string_list(
            value=raw_search["destination_airports"],
            field_name="destination_airports",
            index=index,
        )

        departure_days = _parse_integer_list(
            value=raw_search["departure_days"],
            field_name="departure_days",
            index=index,
        )

        trip_lengths = _parse_integer_list(
            value=raw_search["trip_lengths"],
            field_name="trip_lengths",
            index=index,
        )

        direct_only = raw_search.get(
            "direct_only",
            False,
        )

        if not isinstance(direct_only, bool):
            raise ConfigurationError(
                f"Flexible search {index}: 'direct_only' must be true or false."
            )

        return FlexibleMonthSearch(
            origin=str(raw_search["origin"]).strip().upper(),
            destination_name=str(raw_search["destination_name"]).strip(),
            destination_airports=destination_airports,
            year=int(raw_search["year"]),
            month=int(raw_search["month"]),
            departure_days=departure_days,
            trip_lengths=trip_lengths,
            target_price=Decimal(str(raw_search["target_price"])),
            direct_only=direct_only,
            minimum_alert_drop=Decimal(
                str(
                    raw_search.get(
                        "minimum_alert_drop",
                        "50.00",
                    )
                )
            ),
        )
    except KeyError as exc:
        missing_field = exc.args[0]

        raise ConfigurationError(
            f"Flexible search {index}: required field '{missing_field}' is missing."
        ) from exc
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise ConfigurationError(
            f"Flexible search {index} contains an invalid value: {exc}"
        ) from exc


def _parse_string_list(
    value: Any,
    field_name: str,
    index: int,
) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigurationError(
            f"Flexible search {index}: '{field_name}' must be a non-empty list."
        )

    return tuple(str(item).strip().upper() for item in value)


def _parse_integer_list(
    value: Any,
    field_name: str,
    index: int,
) -> tuple[int, ...]:
    if not isinstance(value, list) or not value:
        raise ConfigurationError(
            f"Flexible search {index}: '{field_name}' must be a non-empty list."
        )

    if any(isinstance(item, bool) for item in value):
        raise ConfigurationError(
            f"Flexible search {index}: '{field_name}' must contain only integers."
        )

    try:
        return tuple(int(item) for item in value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"Flexible search {index}: '{field_name}' must contain only integers."
        ) from exc
