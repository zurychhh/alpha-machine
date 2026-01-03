"""
Rule-Based Agent
Implements trading signals using deterministic technical and sentiment rules.
No AI API calls required - uses weighted scoring system.
"""

from typing import Dict, Optional, List
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
import logging

logger = logging.getLogger(__name__)


class RuleBasedAgent(BaseAgent):
    """
    Rule-based trading agent using weighted technical and sentiment indicators.

    This agent provides a baseline for the multi-agent system without
    requiring any AI API calls. It uses a configurable weighted scoring
    system based on:
    - RSI (oversold/overbought)
    - Price momentum (7-day, 30-day)
    - Volume trend
    - Sentiment scores

    The weights and thresholds can be customized to adjust the agent's
    behavior and sensitivity.
    """

    # Default weights for different factors
    DEFAULT_WEIGHTS = {
        "rsi": 0.25,
        "momentum_7d": 0.20,
        "momentum_30d": 0.15,
        "volume_trend": 0.10,
        "sentiment": 0.30,
    }

    # RSI thresholds
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_NEUTRAL_LOW = 45
    RSI_NEUTRAL_HIGH = 55

    def __init__(
        self,
        name: str = "RuleBasedAgent",
        weight: float = 1.0,
        factor_weights: Dict[str, float] = None,
    ):
        """
        Initialize the rule-based agent.

        Args:
            name: Agent name
            weight: Agent weight in consensus
            factor_weights: Optional custom weights for factors
        """
        super().__init__(name=name, weight=weight)
        self.factor_weights = factor_weights or self.DEFAULT_WEIGHTS.copy()

    def analyze(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> AgentSignal:
        """
        Analyze data and produce a trading signal.

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data with indicators
            sentiment_data: Optional sentiment analysis data
            historical_data: Optional historical price data

        Returns:
            AgentSignal with recommendation
        """
        if not self.validate_inputs(ticker, market_data):
            return self.create_neutral_signal(ticker, "Invalid input data")

        # Extract indicators from market data
        indicators = market_data.get("indicators", market_data)

        # Calculate individual factor scores
        factors = {}
        reasoning_parts = []

        # RSI Score
        rsi_score, rsi_reason = self._score_rsi(indicators.get("rsi"))
        factors["rsi"] = rsi_score
        if rsi_reason:
            reasoning_parts.append(rsi_reason)

        # Momentum Score (7-day)
        momentum_7d_score, momentum_7d_reason = self._score_momentum(
            indicators.get("price_change_7d"), days=7
        )
        factors["momentum_7d"] = momentum_7d_score
        if momentum_7d_reason:
            reasoning_parts.append(momentum_7d_reason)

        # Momentum Score (30-day)
        momentum_30d_score, momentum_30d_reason = self._score_momentum(
            indicators.get("price_change_30d"), days=30
        )
        factors["momentum_30d"] = momentum_30d_score

        # Volume Trend Score
        volume_score, volume_reason = self._score_volume_trend(
            indicators.get("volume_trend")
        )
        factors["volume_trend"] = volume_score
        if volume_reason:
            reasoning_parts.append(volume_reason)

        # Sentiment Score
        sentiment_score, sentiment_reason = self._score_sentiment(sentiment_data)
        factors["sentiment"] = sentiment_score
        if sentiment_reason:
            reasoning_parts.append(sentiment_reason)

        # Calculate weighted total score
        total_score = 0.0
        for factor_name, factor_score in factors.items():
            weight = self.factor_weights.get(factor_name, 0.0)
            total_score += factor_score * weight

        # Calculate confidence based on data availability and agreement
        confidence = self._calculate_confidence(factors)

        # Build reasoning string
        reasoning = "; ".join(reasoning_parts) if reasoning_parts else "Mixed signals"

        return AgentSignal.from_score(
            agent_name=self.name,
            ticker=ticker,
            score=total_score,
            confidence=confidence,
            reasoning=reasoning,
            factors=factors,
        )

    def _score_rsi(self, rsi: Optional[float]) -> tuple[float, str]:
        """
        Score RSI indicator.

        RSI < 30: Oversold (bullish signal)
        RSI > 70: Overbought (bearish signal)
        RSI 45-55: Neutral

        Returns:
            Tuple of (score, reasoning)
        """
        if rsi is None:
            return 0.0, ""

        if rsi <= self.RSI_OVERSOLD:
            # Strongly oversold - bullish contrarian signal
            score = 0.8 + (self.RSI_OVERSOLD - rsi) / self.RSI_OVERSOLD * 0.2
            return min(score, 1.0), f"RSI {rsi:.1f} indicates oversold conditions"

        elif rsi >= self.RSI_OVERBOUGHT:
            # Strongly overbought - bearish contrarian signal
            score = (
                -0.8 - (rsi - self.RSI_OVERBOUGHT) / (100 - self.RSI_OVERBOUGHT) * 0.2
            )
            return max(score, -1.0), f"RSI {rsi:.1f} indicates overbought conditions"

        elif self.RSI_NEUTRAL_LOW <= rsi <= self.RSI_NEUTRAL_HIGH:
            # Neutral zone
            return 0.0, ""

        elif rsi < self.RSI_NEUTRAL_LOW:
            # Slightly oversold
            normalized = (self.RSI_NEUTRAL_LOW - rsi) / (
                self.RSI_NEUTRAL_LOW - self.RSI_OVERSOLD
            )
            return normalized * 0.5, f"RSI {rsi:.1f} suggests potential upside"

        else:  # rsi > self.RSI_NEUTRAL_HIGH
            # Slightly overbought
            normalized = (rsi - self.RSI_NEUTRAL_HIGH) / (
                self.RSI_OVERBOUGHT - self.RSI_NEUTRAL_HIGH
            )
            return -normalized * 0.5, f"RSI {rsi:.1f} suggests potential resistance"

    def _score_momentum(
        self, price_change: Optional[float], days: int
    ) -> tuple[float, str]:
        """
        Score price momentum.

        Strong momentum (>10%): Strong signal
        Moderate momentum (3-10%): Moderate signal
        Weak momentum (<3%): Weak/no signal

        Returns:
            Tuple of (score, reasoning)
        """
        if price_change is None:
            return 0.0, ""

        # Define thresholds based on timeframe
        if days <= 7:
            strong_threshold = 8.0
            moderate_threshold = 3.0
        else:
            strong_threshold = 15.0
            moderate_threshold = 5.0

        abs_change = abs(price_change)
        direction = 1 if price_change >= 0 else -1

        if abs_change >= strong_threshold:
            score = direction * 0.8
            trend = "strong bullish" if direction > 0 else "strong bearish"
            reason = f"{days}-day momentum {price_change:+.1f}% shows {trend} trend"
        elif abs_change >= moderate_threshold:
            score = direction * 0.4
            trend = "bullish" if direction > 0 else "bearish"
            reason = (
                f"{days}-day momentum {price_change:+.1f}% indicates {trend} direction"
            )
        else:
            score = direction * 0.1
            reason = ""

        return score, reason

    def _score_volume_trend(self, volume_trend: Optional[str]) -> tuple[float, str]:
        """
        Score volume trend.

        Increasing volume with price up: Confirms bullish trend
        Decreasing volume: Weakens trend signal

        Returns:
            Tuple of (score, reasoning)
        """
        if not volume_trend:
            return 0.0, ""

        volume_trend = volume_trend.lower()

        if volume_trend == "increasing":
            return 0.3, "Volume increasing supports momentum"
        elif volume_trend == "decreasing":
            return -0.2, "Declining volume suggests weakening trend"
        else:
            return 0.0, ""

    def _score_sentiment(self, sentiment_data: Optional[Dict]) -> tuple[float, str]:
        """
        Score sentiment data.

        Uses combined sentiment score and total mentions for weighting.

        Returns:
            Tuple of (score, reasoning)
        """
        if not sentiment_data:
            return 0.0, ""

        combined_sentiment = sentiment_data.get("combined_sentiment", 0.0)
        sentiment_label = sentiment_data.get("sentiment_label", "neutral")
        total_mentions = sentiment_data.get("total_mentions", 0)

        # Weight sentiment by mention volume (more mentions = more reliable)
        # Cap at 100 mentions for full weight
        mention_weight = min(total_mentions / 100, 1.0) if total_mentions > 0 else 0.5

        score = combined_sentiment * mention_weight

        if abs(score) > 0.3:
            direction = "bullish" if score > 0 else "bearish"
            reason = f"Sentiment ({sentiment_label}) with {total_mentions} mentions is {direction}"
        else:
            reason = ""

        return score, reason

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """
        Calculate confidence based on factor agreement.

        Confidence is higher when:
        - More factors have non-zero values (more data available)
        - Factors agree in direction (all bullish or all bearish)

        Returns:
            Confidence score (0.0 to 1.0)
        """
        non_zero = [f for f in factors.values() if abs(f) > 0.1]

        if len(non_zero) == 0:
            return 0.0

        # Data availability component (40%)
        data_confidence = len(non_zero) / len(factors) * 0.4

        # Agreement component (60%)
        positive = sum(1 for f in non_zero if f > 0)
        negative = len(non_zero) - positive

        if len(non_zero) > 0:
            agreement_ratio = max(positive, negative) / len(non_zero)
            agreement_confidence = agreement_ratio * 0.6
        else:
            agreement_confidence = 0.0

        return min(data_confidence + agreement_confidence, 1.0)
