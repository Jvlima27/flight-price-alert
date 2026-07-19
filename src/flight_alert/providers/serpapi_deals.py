import json
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flight_alert.models import (
    FlexibleDealResult,
    FlexibleMonthSearch,
)
from flight_alert.providers.base import (
    NoFlightResultsError,
    ProviderError,
)
from flight_alert.providers.flexible_base import (
    FlexibleFlightDealsProvider,
)

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


class SerpApiFlexibleDealsProvider(FlexibleFlightDealsProvider):
    """Retrieve flexible flight deals through SerpApi."""

    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("SerpApi API key cannot be empty.")

        self._api_key = api_key.strip()
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        return "serpapi_google_flights_deals"

    def search(
        self,
        search: FlexibleMonthSearch,
    ) -> FlexibleDealResult:
        parameters = self._build_parameters(search)
        request_url = f"{SERPAPI_ENDPOINT}?{urlencode(parameters)}"

        request = Request(
            url=request_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "flight-price-alert/0.1.0",
            },
            method="GET",
        )

        payload = self._perform_request(request)
        matching_deals = self._extract_matching_deals(
            payload=payload,
            search=search,
        )

        if not matching_deals:
            airports = ", ".join(search.destination_airports)

            raise NoFlightResultsError(
                f"No flexible deals were returned for {search.destination_name} ({airports})."
            )

        cheapest_deal = min(
            matching_deals,
            key=self._extract_price,
        )

        return self._create_result(
            search=search,
            deal=cheapest_deal,
        )

    def _build_parameters(
        self,
        search: FlexibleMonthSearch,
    ) -> dict[str, str | int]:
        outbound_window = (
            f"{search.outbound_start_date.isoformat()},{search.outbound_end_date.isoformat()}"
        )

        trip_length = f"{search.minimum_trip_days},{search.maximum_trip_days}"

        return {
            "engine": "google_flights_deals",
            "api_key": self._api_key,
            "departure_id": search.origin,
            "outbound_date": outbound_window,
            "trip_length": trip_length,
            "type": 1,
            "currency": "BRL",
            "gl": "br",
            "hl": "pt",
            "travel_class": 1,
            "adults": 1,
            "stops": 1 if search.direct_only else 0,
        }

    def _perform_request(
        self,
        request: Request,
    ) -> dict[str, Any]:
        try:
            with urlopen(
                request,
                timeout=self._timeout_seconds,
            ) as response:
                payload: Any = json.load(response)
        except HTTPError as exc:
            raise ProviderError(
                f"SerpApi Deals rejected the request with HTTP {exc.code}."
            ) from exc
        except URLError as exc:
            raise ProviderError("Could not connect to SerpApi Deals.") from exc
        except TimeoutError as exc:
            raise ProviderError("SerpApi Deals request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("SerpApi Deals returned invalid JSON.") from exc

        if not isinstance(payload, dict):
            raise ProviderError("SerpApi Deals returned an unexpected response.")

        error_message = payload.get("error")

        if isinstance(error_message, str):
            normalized_error = error_message.casefold()

            if (
                "hasn't returned any results" in normalized_error
                or "no results" in normalized_error
            ):
                raise NoFlightResultsError(error_message)

            raise ProviderError(f"SerpApi Deals returned an error: {error_message}")

        return payload

    @staticmethod
    def _extract_matching_deals(
        payload: dict[str, Any],
        search: FlexibleMonthSearch,
    ) -> list[dict[str, Any]]:
        raw_deals = payload.get("deals", [])

        if not isinstance(raw_deals, list):
            return []

        allowed_airports = set(search.destination_airports)

        return [
            deal
            for deal in raw_deals
            if isinstance(deal, dict)
            and str(
                deal.get(
                    "arrival_airport_code",
                    "",
                )
            ).upper()
            in allowed_airports
            and deal.get("price") is not None
            and deal.get("start_date") is not None
            and deal.get("end_date") is not None
        ]

    def _create_result(
        self,
        search: FlexibleMonthSearch,
        deal: dict[str, Any],
    ) -> FlexibleDealResult:
        try:
            departure_date = date.fromisoformat(str(deal["start_date"]))

            return_date = date.fromisoformat(str(deal["end_date"]))

            price = self._extract_price(deal)
        except (KeyError, ValueError) as exc:
            raise ProviderError("A flexible deal contained invalid dates.") from exc

        airline = str(
            deal.get(
                "airline",
                "Companhia não informada",
            )
        ).strip()

        booking_url_value = deal.get("flight_link")

        booking_url = (
            booking_url_value.strip()
            if isinstance(booking_url_value, str) and booking_url_value.strip()
            else None
        )

        return FlexibleDealResult(
            search=search,
            price=price,
            origin=str(
                deal.get(
                    "departure_airport_code",
                    search.origin,
                )
            ).upper(),
            destination=str(deal["arrival_airport_code"]).upper(),
            departure_date=departure_date,
            return_date=return_date,
            airline=(airline if airline else "Companhia não informada"),
            source=self.name,
            booking_url=booking_url,
        )

    @staticmethod
    def _extract_price(
        deal: dict[str, Any],
    ) -> Decimal:
        try:
            price = Decimal(str(deal["price"]))
        except (
            KeyError,
            InvalidOperation,
            ValueError,
        ) as exc:
            raise ProviderError("A flexible deal contained an invalid price.") from exc

        if price <= Decimal("0"):
            raise ProviderError("A flexible deal contained a non-positive price.")

        return price
