import json
from decimal import Decimal
from pathlib import Path

from flight_alert.config import load_routes


def test_load_routes_from_json(tmp_path: Path) -> None:
    routes_file = tmp_path / "routes.json"

    routes_file.write_text(
        json.dumps(
            {
                "routes": [
                    {
                        "origin": "vix",
                        "destination": "scl",
                        "departure_date": "2026-10-15",
                        "return_date": "2026-10-22",
                        "target_price": "2500.00",
                        "direct_only": False,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    routes = load_routes(routes_file)

    assert len(routes) == 1
    assert routes[0].origin == "VIX"
    assert routes[0].destination == "SCL"
    assert routes[0].target_price == Decimal("2500.00")
