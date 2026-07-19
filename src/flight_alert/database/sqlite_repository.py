import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from flight_alert.models import PriceResult, Route

CENTS_MULTIPLIER = Decimal("100")
INTEGER_PRECISION = Decimal("1")
MONEY_PRECISION = Decimal("0.01")


class SQLitePriceRepository:
    """Store and retrieve flight price history using SQLite."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def initialize(self) -> None:
        """Create the database structure when it does not exist."""

        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_key TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    departure_date TEXT NOT NULL,
                    return_date TEXT,
                    direct_only INTEGER NOT NULL,
                    target_price_cents INTEGER NOT NULL,
                    price_cents INTEGER NOT NULL,
                    airline TEXT NOT NULL,
                    source TEXT NOT NULL,
                    booking_url TEXT,
                    checked_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_price_history_route_checked_at
                ON price_history (route_key, checked_at DESC)
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_key TEXT NOT NULL,
                    price_cents INTEGER NOT NULL,
                    channel TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    sent_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_alert_history_route_sent_at
                ON alert_history (route_key, sent_at DESC)
                """
            )

    def save(self, result: PriceResult) -> None:
        """Save a price result in the history."""

        route = result.route

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO price_history (
                    route_key,
                    origin,
                    destination,
                    departure_date,
                    return_date,
                    direct_only,
                    target_price_cents,
                    price_cents,
                    airline,
                    source,
                    booking_url,
                    checked_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self._create_result_key(result),
                    route.origin,
                    route.destination,
                    route.departure_date.isoformat(),
                    (route.return_date.isoformat() if route.return_date is not None else None),
                    int(route.direct_only),
                    self._to_cents(route.target_price),
                    self._to_cents(result.price),
                    result.airline,
                    result.source,
                    result.booking_url,
                    result.checked_at.isoformat(),
                ),
            )

    def get_latest_price(
        self,
        route: Route,
        monitor_key: str | None = None,
    ) -> Decimal | None:
        """Return the most recently recorded price for a route."""

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT price_cents
                FROM price_history
                WHERE route_key = ?
                ORDER BY checked_at DESC, id DESC
                LIMIT 1
                """,
                (
                    self._create_route_key(
                        route,
                        monitor_key=monitor_key,
                    ),
                ),
            ).fetchone()

        if row is None:
            return None

        return self._from_cents(row[0])

    def get_lowest_price(
        self,
        route: Route,
        monitor_key: str | None = None,
    ) -> Decimal | None:
        """Return the lowest previously recorded price for a route."""

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT MIN(price_cents)
                FROM price_history
                WHERE route_key = ?
                """,
                (
                    self._create_route_key(
                        route,
                        monitor_key=monitor_key,
                    ),
                ),
            ).fetchone()

        if row is None or row[0] is None:
            return None

        return self._from_cents(row[0])

    def count(
        self,
        route: Route,
        monitor_key: str | None = None,
    ) -> int:
        """Return the number of saved results for a route."""

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM price_history
                WHERE route_key = ?
                """,
                (
                    self._create_route_key(
                        route,
                        monitor_key=monitor_key,
                    ),
                ),
            ).fetchone()

        return int(row[0])

    def save_alert(
        self,
        result: PriceResult,
        channel: str,
        reason: str,
    ) -> None:
        """Record a successfully sent price alert."""

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO alert_history (
                    route_key,
                    price_cents,
                    channel,
                    reason,
                    sent_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self._create_result_key(result),
                    self._to_cents(result.price),
                    channel,
                    reason,
                    datetime.now(UTC).isoformat(),
                ),
            )

    def get_latest_alert_price(
        self,
        route: Route,
        monitor_key: str | None = None,
    ) -> Decimal | None:
        """Return the price used in the latest sent alert."""

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT price_cents
                FROM alert_history
                WHERE route_key = ?
                ORDER BY sent_at DESC, id DESC
                LIMIT 1
                """,
                (
                    self._create_route_key(
                        route,
                        monitor_key=monitor_key,
                    ),
                ),
            ).fetchone()

        if row is None:
            return None

        return self._from_cents(row[0])

    def count_alerts(
        self,
        route: Route,
        monitor_key: str | None = None,
    ) -> int:
        """Return the number of alerts sent for a route."""

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM alert_history
                WHERE route_key = ?
                """,
                (
                    self._create_route_key(
                        route,
                        monitor_key=monitor_key,
                    ),
                ),
            ).fetchone()

        return int(row[0])

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(self.database_path)

        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _create_route_key(
        route: Route,
        monitor_key: str | None = None,
    ) -> str:
        if monitor_key is not None:
            return monitor_key

        return_date = route.return_date.isoformat() if route.return_date is not None else ""

        return "|".join(
            [
                route.origin,
                route.destination,
                route.departure_date.isoformat(),
                return_date,
                str(int(route.direct_only)),
            ]
        )

    @classmethod
    def _create_result_key(
        cls,
        result: PriceResult,
    ) -> str:
        return cls._create_route_key(
            route=result.route,
            monitor_key=result.monitor_key,
        )

    @staticmethod
    def _to_cents(value: Decimal) -> int:
        return int(
            (value * CENTS_MULTIPLIER).quantize(
                INTEGER_PRECISION,
                rounding=ROUND_HALF_UP,
            )
        )

    @staticmethod
    def _from_cents(value: int) -> Decimal:
        return (Decimal(value) / CENTS_MULTIPLIER).quantize(MONEY_PRECISION)
