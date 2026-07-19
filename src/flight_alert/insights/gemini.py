from typing import Any

from google import genai

from flight_alert.insights.base import PriceInsightGenerator
from flight_alert.models import (
    AlertDecision,
    PriceAnalysis,
    PriceHistoryAnalysis,
)


class InsightError(RuntimeError):
    """Raised when an AI insight cannot be generated."""


class GeminiPriceInsightGenerator(PriceInsightGenerator):
    """Generate concise flight price insights using Gemini."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.1-flash-lite",
        client: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("Gemini API key cannot be empty.")

        if not model.strip():
            raise ValueError("Gemini model cannot be empty.")

        self._model = model.strip()
        self._client = client or genai.Client(
            api_key=api_key.strip(),
        )

    @property
    def name(self) -> str:
        return "gemini"

    def generate(
        self,
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
        alert_decision: AlertDecision,
    ) -> str:
        prompt = self._build_prompt(
            price_analysis=price_analysis,
            history_analysis=history_analysis,
            alert_decision=alert_decision,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
        except Exception as exc:
            raise InsightError("Gemini could not generate the price insight.") from exc

        insight = str(response.text or "").strip()

        if not insight:
            raise InsightError("Gemini returned an empty price insight.")

        return insight[:1000]

    @staticmethod
    def _build_prompt(
        price_analysis: PriceAnalysis,
        history_analysis: PriceHistoryAnalysis,
        alert_decision: AlertDecision,
    ) -> str:
        result = price_analysis.result
        route = result.route

        return_date = (
            route.return_date.isoformat() if route.return_date is not None else "somente ida"
        )

        previous_price = (
            f"R$ {history_analysis.previous_price:.2f}"
            if history_analysis.previous_price is not None
            else "não disponível"
        )

        previous_lowest = (
            f"R$ {history_analysis.previous_lowest_price:.2f}"
            if history_analysis.previous_lowest_price is not None
            else "não disponível"
        )

        difference_percentage = f"{price_analysis.difference_percentage:.2f}"

        prompt = f"""
Você escreve análises curtas para alertas de preços de passagens.

Use somente os dados fornecidos.
Não invente informações.
Não faça previsões sobre preços futuros.
Não diga que a compra é garantidamente recomendada.
Responda em português brasileiro.
Use no máximo duas frases e 300 caracteres.
Não use Markdown.

Rota: {route.origin} para {route.destination}
Data de ida: {route.departure_date.isoformat()}
Data de volta: {return_date}
Preço atual: R$ {result.price:.2f}
Preço-alvo: R$ {route.target_price:.2f}
Diferença percentual para a meta: {difference_percentage}%
Preço anterior: {previous_price}
Menor preço anterior: {previous_lowest}
Novo menor preço: {history_analysis.is_new_lowest}
Motivo do alerta: {alert_decision.reason.value}
"""

        return prompt.strip()
