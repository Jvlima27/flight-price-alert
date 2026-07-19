import logging

from flight_alert.database import SQLitePriceRepository
from flight_alert.insights import (
    InsightError,
    PriceInsightGenerator,
)
from flight_alert.models import (
    AlertDecision,
    PriceAnalysis,
    PriceHistoryAnalysis,
    PriceResult,
    PriceStatus,
)
from flight_alert.notifications import PriceAlertNotifier
from flight_alert.services.alert_policy import decide_alert
from flight_alert.services.history_analyzer import (
    analyze_price_history,
)
from flight_alert.services.price_analyzer import analyze_price

logger = logging.getLogger(__name__)


class PriceMonitoringEngine:
    """Analyze, persist and notify flight price results."""

    def __init__(
        self,
        repository: SQLitePriceRepository,
        notifier: PriceAlertNotifier | None = None,
        insight_generator: PriceInsightGenerator | None = None,
    ) -> None:
        self.repository = repository
        self.notifier = notifier
        self.insight_generator = insight_generator

    def initialize(self) -> None:
        self.repository.initialize()

    def process(self, result: PriceResult) -> None:
        route = result.route

        previous_price = self.repository.get_latest_price(
            route,
            monitor_key=result.monitor_key,
        )

        previous_lowest_price = self.repository.get_lowest_price(
            route,
            monitor_key=result.monitor_key,
        )

        last_alerted_price = self.repository.get_latest_alert_price(
            route,
            monitor_key=result.monitor_key,
        )

        price_analysis = analyze_price(result)

        history_analysis = analyze_price_history(
            result=result,
            previous_price=previous_price,
            previous_lowest_price=previous_lowest_price,
        )

        alert_decision = decide_alert(
            price_analysis=price_analysis,
            history_analysis=history_analysis,
            last_alerted_price=last_alerted_price,
            minimum_alert_drop=route.minimum_alert_drop,
        )

        self.repository.save(result)

        self._log_price_analysis(price_analysis)
        self._log_history_analysis(history_analysis)

        self._process_alert(
            decision=alert_decision,
            price_analysis=price_analysis,
            history_analysis=history_analysis,
        )

    def _process_alert(
        self,
        decision: AlertDecision,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
    ) -> None:
        if not decision.should_notify:
            logger.info(
                "Notification suppressed. Reason: %s.",
                decision.reason.value,
            )
            return

        if self.notifier is None:
            logger.warning("An alert should be sent, but no notifier is configured.")
            return

        insight = self._generate_insight(
            decision=decision,
            price_analysis=price_analysis,
            history_analysis=history_analysis,
        )

        self.notifier.send(
            price_analysis=price_analysis,
            history_analysis=history_analysis,
            insight=insight,
        )

        self.repository.save_alert(
            result=price_analysis.result,
            channel=self.notifier.name,
            reason=decision.reason.value,
        )

        logger.info(
            "Price alert sent successfully. Reason: %s.",
            decision.reason.value,
        )

    def _generate_insight(
        self,
        decision: AlertDecision,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
    ) -> str | None:
        if self.insight_generator is None:
            return None

        try:
            insight = self.insight_generator.generate(
                price_analysis=price_analysis,
                history_analysis=history_analysis,
                alert_decision=decision,
            )
        except InsightError as exc:
            logger.warning(
                "AI insight could not be generated: %s",
                exc,
            )
            return None

        logger.info(
            "AI insight generated successfully using %s.",
            self.insight_generator.name,
        )

        return insight

    @staticmethod
    def _log_price_analysis(
        analysis: PriceAnalysis,
    ) -> None:
        result = analysis.result
        route = result.route

        logger.info(
            "Price found: %s -> %s | airline=%s | price=R$ %s | target=R$ %s | source=%s",
            route.origin,
            route.destination,
            result.airline,
            f"{result.price:.2f}",
            f"{route.target_price:.2f}",
            result.source,
        )

        if analysis.status is PriceStatus.ABOVE_TARGET:
            logger.info(
                "Price is R$ %s above the target (%s%%).",
                f"{abs(analysis.difference):.2f}",
                f"{abs(analysis.difference_percentage):.2f}",
            )
            return

        logger.info(
            "Price reached the target. Savings: R$ %s (%s%%).",
            f"{analysis.difference:.2f}",
            f"{analysis.difference_percentage:.2f}",
        )

    @staticmethod
    def _log_history_analysis(
        analysis: PriceHistoryAnalysis,
    ) -> None:
        if analysis.previous_price is None:
            logger.info("This is the first recorded price for this monitor.")
        elif analysis.change_amount is None:
            logger.info("Historical price variation is unavailable.")
        elif analysis.change_amount < 0:
            logger.info(
                "Price dropped by R$ %s (%s%%) since the previous check.",
                f"{abs(analysis.change_amount):.2f}",
                f"{abs(analysis.change_percentage):.2f}",
            )
        elif analysis.change_amount > 0:
            logger.info(
                "Price increased by R$ %s (%s%%) since the previous check.",
                f"{analysis.change_amount:.2f}",
                f"{analysis.change_percentage:.2f}",
            )
        else:
            logger.info("Price has not changed since the previous check.")

        if analysis.is_new_lowest:
            logger.info("This is a new lowest recorded price.")
