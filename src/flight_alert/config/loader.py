import json
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from flight_alert.models import Route


class ConfigurationError(Exception):
    """Raised when the application configuration is invalid."""


def load_routes(file_path: Path) -> list[Route]:
    """Load monitored routes from a JSON file."""

    try:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"Configuration file not found: {file_path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"Invalid JSON in {file_path} at line {exc.lineno}, column {exc.colno}."
        ) from exc

    if not isinstance(data, dict):
        raise ConfigurationError("The configuration root must be a JSON object.")

    raw_routes = data.get("routes")

    if not isinstance(raw_routes, list) or not raw_routes:
        raise ConfigurationError("The configuration must contain a non-empty 'routes' list.")

    return [_parse_route(raw_route, index) for index, raw_route in enumerate(raw_routes, start=1)]


def _parse_route(raw_route: Any, index: int) -> Route:
    if not isinstance(raw_route, dict):
        raise ConfigurationError(f"Route {index} must be a JSON object.")

    direct_only = raw_route.get("direct_only", False)

    if not isinstance(direct_only, bool):
        raise ConfigurationError(f"Route {index}: 'direct_only' must be true or false.")

    try:
        return_date_value = raw_route.get("return_date")

        return Route(
            origin=str(raw_route["origin"]).strip().upper(),
            destination=str(raw_route["destination"]).strip().upper(),
            departure_date=date.fromisoformat(str(raw_route["departure_date"])),
            return_date=(date.fromisoformat(str(return_date_value)) if return_date_value else None),
            target_price=Decimal(str(raw_route["target_price"])),
            direct_only=direct_only,
        )
    except KeyError as exc:
        missing_field = exc.args[0]

        raise ConfigurationError(
            f"Route {index}: required field '{missing_field}' is missing."
        ) from exc
    except (ValueError, InvalidOperation) as exc:
        raise ConfigurationError(f"Route {index} contains an invalid value: {exc}") from exc
