import json
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from flight_alert.models import PriceResult, Route
from flight_alert.providers.base import (
    FlightPriceProvider,
    NoFlightResultsError,
    ProviderError,
)

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


class SerpApiFlightPriceProvider(FlightPriceProvider):
    """Retrieve real flight prices from Google Flights through SerpApi."""

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
        return "serpapi_google_flights"

    def search(self, route: Route) -> PriceResult:
        parameters = self._build_parameters(route)
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
        offers = self._extract_offers(payload)

        if not offers:
            raise NoFlightResultsError(
                f"No flight offers were found for {route.origin} -> {route.destination}."
            )

        cheapest_offer = min(
            offers,
            key=self._extract_price,
        )

        return PriceResult(
            route=route,
            price=self._extract_price(cheapest_offer),
            airline=self._extract_airlines(cheapest_offer),
            source=self.name,
            booking_url=self._extract_booking_url(payload),
        )

    def _build_parameters(
        self,
        route: Route,
    ) -> dict[str, str | int]:
        parameters: dict[str, str | int] = {
            "engine": "google_flights",
            "api_key": self._api_key,
            "departure_id": route.origin,
            "arrival_id": route.destination,
            "outbound_date": route.departure_date.isoformat(),
            "currency": "BRL",
            "gl": "br",
            "hl": "pt",
            "travel_class": 1,
            "adults": 1,
            "sort_by": 2,
            "stops": 1 if route.direct_only else 0,
            "deep_search": "true",
        }

        if route.return_date is None:
            parameters["type"] = 2
        else:
            parameters["type"] = 1
            parameters["return_date"] = route.return_date.isoformat()

        return parameters

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
            raise ProviderError(f"SerpApi rejected the request with HTTP {exc.code}.") from exc
        except URLError as exc:
            raise ProviderError("Could not connect to SerpApi.") from exc
        except TimeoutError as exc:
            raise ProviderError("SerpApi request timed out.") from exc
        except json.JSONDecodeError as exc:
            raise ProviderError("SerpApi returned an invalid JSON response.") from exc

        if not isinstance(payload, dict):
            raise ProviderError("SerpApi returned an unexpected response format.")

        error_message = payload.get("error")

        if isinstance(error_message, str):
            normalized_error = error_message.casefold()

            if (
                "hasn't returned any results" in normalized_error
                or "no results" in normalized_error
            ):
                raise NoFlightResultsError(error_message)

            raise ProviderError(f"SerpApi returned an error: {error_message}")

        return payload

    @staticmethod
    def _extract_offers(
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        offers: list[dict[str, Any]] = []

        for section_name in ("best_flights", "other_flights"):
            section = payload.get(section_name, [])

            if not isinstance(section, list):
                continue

            offers.extend(
                offer
                for offer in section
                if isinstance(offer, dict) and offer.get("price") is not None
            )

        return offers

    @staticmethod
    def _extract_price(
        offer: dict[str, Any],
    ) -> Decimal:
        try:
            price = Decimal(str(offer["price"]))
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise ProviderError("A flight offer contained an invalid price.") from exc

        if price <= Decimal("0"):
            raise ProviderError("A flight offer contained a non-positive price.")

        return price

    @staticmethod
    def _extract_airlines(
        offer: dict[str, Any],
    ) -> str:
        flights = offer.get("flights", [])

        if not isinstance(flights, list):
            return "Companhia não informada"

        airlines: list[str] = []

        for flight in flights:
            if not isinstance(flight, dict):
                continue

            airline = flight.get("airline")

            if isinstance(airline, str) and airline.strip() and airline not in airlines:
                airlines.append(airline.strip())

        if not airlines:
            return "Companhia não informada"

        return " + ".join(airlines)

    @staticmethod
    def _extract_booking_url(
        payload: dict[str, Any],
    ) -> str | None:
        metadata = payload.get("search_metadata")

        if not isinstance(metadata, dict):
            return None

        google_flights_url = metadata.get("google_flights_url")

        if isinstance(google_flights_url, str) and google_flights_url.strip():
            return google_flights_url.strip()

        return None
