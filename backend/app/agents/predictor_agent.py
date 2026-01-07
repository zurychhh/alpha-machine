"""
Predictor Agent - Technical Analysis Agent
Uses technical indicators and pattern recognition for price prediction.
Simple rule-based implementation for MVP (can be enhanced with ML later).
"""

from typing import Dict, Optional, List
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
import logging

logger = logging.getLogger(__name__)


class PredictorAgent(BaseAgent):
    """
    Technical predictor agent using pattern recognition and indicators.

    For MVP, this uses enhanced rule-based logic focusing on:
    - Multiple technical indicators combination
    - Price pattern recognition
    - Trend strength analysis
    - Support/resistance approximation

    Future enhancement: Replace with LSTM or transformer model.
    """

    # Technical indicator thresholds
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_BULLISH_ZONE = 50
    RSI_BEARISH_ZONE = 50

    def __init__(
        self,
        name: str = "TechnicalPredictorAgent",
        weight: float = 1.0,
    ):
        """
        Initialize the predictor agent.

        Args:
            name: Agent name
            weight: Weight in consensus algorithm
        """
        super().__init__(name=name, weight=weight)

    def analyze(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> AgentSignal:
        """
        Perform technical analysis and prediction.

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data (price, volume, indicators)
            sentiment_data: Sentiment analysis data (used for confirmation)
            historical_data: Historical price data

        Returns:
            AgentSignal with technical prediction
        """
        if not self.validate_inputs(ticker, market_data):
            return self.create_neutral_signal(ticker, "Invalid input data")

        # Extract indicators
        indicators = market_data.get("indicators", market_data)

        # Calculate individual technical scores
        factors = {}
        reasoning_parts = []

        # 1. RSI Analysis
        rsi_score, rsi_conf, rsi_reason = self._analyze_rsi(indicators.get("rsi"))
        factors["rsi_signal"] = rsi_score
        if rsi_reason:
            reasoning_parts.append(rsi_reason)

        # 2. Moving Average Analysis
        ma_score, ma_conf, ma_reason = self._analyze_moving_averages(
            market_data.get("current_price", market_data.get("price")),
            indicators.get("sma_50"),
            indicators.get("sma_200"),
        )
        factors["ma_signal"] = ma_score
        if ma_reason:
            reasoning_parts.append(ma_reason)

        # 3. Momentum Analysis
        mom_score, mom_conf, mom_reason = self._analyze_momentum(
            indicators.get("price_change_7d"),
            indicators.get("price_change_30d"),
        )
        factors["momentum_signal"] = mom_score
        if mom_reason:
            reasoning_parts.append(mom_reason)

        # 4. Volume Analysis
        vol_score, vol_conf, vol_reason = self._analyze_volume(
            indicators.get("volume_trend"),
            indicators.get("volume_change"),
        )
        factors["volume_signal"] = vol_score
        if vol_reason:
            reasoning_parts.append(vol_reason)

        # 5. Trend Strength (from historical data)
        trend_score, trend_conf, trend_reason = self._analyze_trend(historical_data)
        factors["trend_signal"] = trend_score
        if trend_reason:
            reasoning_parts.append(trend_reason)

        # 6. Sentiment Analysis (Reddit + News)
        sent_score, sent_conf, sent_reason = self._analyze_sentiment(sentiment_data)
        factors["sentiment_signal"] = sent_score
        if sent_reason:
            reasoning_parts.append(sent_reason)

        # Calculate weighted final score
        # Weights adjusted to include sentiment (20% weight, sum = 1.0)
        weights = {
            "rsi_signal": 0.16,       # was 0.20
            "ma_signal": 0.20,        # was 0.25
            "momentum_signal": 0.20,  # was 0.25
            "volume_signal": 0.08,    # was 0.10
            "trend_signal": 0.16,     # was 0.20
            "sentiment_signal": 0.20, # NEW: sentiment gets 20% weight
        }

        # Calculate weighted score
        total_score = 0.0
        total_weight = 0.0
        for factor_name, factor_score in factors.items():
            w = weights.get(factor_name, 0.0)
            total_score += factor_score * w
            total_weight += w

        if total_weight > 0:
            total_score = total_score / total_weight * total_weight

        # Calculate confidence based on signal agreement
        confidence = self._calculate_confidence(factors)

        # Build reasoning
        reasoning = (
            "; ".join(reasoning_parts)
            if reasoning_parts
            else "Insufficient technical data"
        )

        return AgentSignal.from_score(
            agent_name=self.name,
            ticker=ticker,
            score=total_score,
            confidence=confidence,
            reasoning=f"[Technical] {reasoning}",
            factors=factors,
        )

    def _analyze_rsi(self, rsi: Optional[float]) -> tuple:
        """
        Analyze RSI indicator.

        Returns: (score, confidence, reasoning)
        """
        if rsi is None:
            return 0.0, 0.0, ""

        if rsi <= self.RSI_OVERSOLD:
            # Oversold - bullish reversal signal
            score = 0.6 + (self.RSI_OVERSOLD - rsi) / self.RSI_OVERSOLD * 0.4
            return (
                min(score, 1.0),
                0.8,
                f"RSI {rsi:.0f} oversold - bullish reversal likely",
            )

        elif rsi >= self.RSI_OVERBOUGHT:
            # Overbought - bearish reversal signal
            score = (
                -0.6 - (rsi - self.RSI_OVERBOUGHT) / (100 - self.RSI_OVERBOUGHT) * 0.4
            )
            return max(score, -1.0), 0.8, f"RSI {rsi:.0f} overbought - correction risk"

        elif rsi > self.RSI_BULLISH_ZONE:
            # Bullish zone but not overbought
            strength = (rsi - 50) / (self.RSI_OVERBOUGHT - 50)
            return strength * 0.3, 0.5, f"RSI {rsi:.0f} bullish momentum"

        elif rsi < self.RSI_BEARISH_ZONE:
            # Bearish zone but not oversold
            strength = (50 - rsi) / (50 - self.RSI_OVERSOLD)
            return -strength * 0.3, 0.5, f"RSI {rsi:.0f} bearish pressure"

        else:
            return 0.0, 0.3, ""

    def _analyze_moving_averages(
        self,
        current_price: Optional[float],
        sma_50: Optional[float],
        sma_200: Optional[float],
    ) -> tuple:
        """
        Analyze moving average positions and crossovers.

        Returns: (score, confidence, reasoning)
        """
        if current_price is None:
            return 0.0, 0.0, ""

        try:
            price = float(current_price)
        except (ValueError, TypeError):
            return 0.0, 0.0, ""

        score = 0.0
        signals = []
        confidence = 0.5

        # Price vs 50-day SMA
        if sma_50:
            pct_from_50 = ((price - sma_50) / sma_50) * 100
            if pct_from_50 > 5:
                score += 0.3
                signals.append(f"above 50-SMA by {pct_from_50:.1f}%")
            elif pct_from_50 < -5:
                score -= 0.3
                signals.append(f"below 50-SMA by {abs(pct_from_50):.1f}%")

        # Price vs 200-day SMA
        if sma_200:
            pct_from_200 = ((price - sma_200) / sma_200) * 100
            if pct_from_200 > 10:
                score += 0.3
                confidence = 0.7
            elif pct_from_200 < -10:
                score -= 0.3
                confidence = 0.7

        # Golden/Death Cross (50 vs 200)
        if sma_50 and sma_200:
            if sma_50 > sma_200:
                score += 0.2
                signals.append("golden cross pattern")
                confidence = 0.8
            elif sma_50 < sma_200:
                score -= 0.2
                signals.append("death cross pattern")
                confidence = 0.8

        reasoning = "Price " + ", ".join(signals) if signals else ""
        return max(-1.0, min(1.0, score)), confidence, reasoning

    def _analyze_momentum(
        self,
        change_7d: Optional[float],
        change_30d: Optional[float],
    ) -> tuple:
        """
        Analyze price momentum over different timeframes.

        Returns: (score, confidence, reasoning)
        """
        if change_7d is None and change_30d is None:
            return 0.0, 0.0, ""

        score = 0.0
        signals = []
        confidence = 0.5

        # 7-day momentum
        if change_7d is not None:
            if change_7d > 10:
                score += 0.5
                signals.append(f"strong 7d momentum +{change_7d:.1f}%")
                confidence = 0.7
            elif change_7d > 3:
                score += 0.2
                signals.append(f"positive 7d +{change_7d:.1f}%")
            elif change_7d < -10:
                score -= 0.5
                signals.append(f"weak 7d momentum {change_7d:.1f}%")
                confidence = 0.7
            elif change_7d < -3:
                score -= 0.2

        # 30-day momentum
        if change_30d is not None:
            if change_30d > 15:
                score += 0.4
                signals.append(f"strong 30d trend +{change_30d:.1f}%")
            elif change_30d > 5:
                score += 0.15
            elif change_30d < -15:
                score -= 0.4
                signals.append(f"downtrend 30d {change_30d:.1f}%")
            elif change_30d < -5:
                score -= 0.15

        # Check for momentum divergence (7d vs 30d)
        if change_7d is not None and change_30d is not None:
            if change_7d > 0 and change_30d < 0:
                signals.append("potential reversal forming")
            elif change_7d < 0 and change_30d > 0:
                signals.append("pullback in uptrend")

        reasoning = "; ".join(signals) if signals else ""
        return max(-1.0, min(1.0, score)), confidence, reasoning

    def _analyze_volume(
        self,
        volume_trend: Optional[str],
        volume_change: Optional[float],
    ) -> tuple:
        """
        Analyze volume patterns.

        Returns: (score, confidence, reasoning)
        """
        if not volume_trend and volume_change is None:
            return 0.0, 0.0, ""

        score = 0.0
        confidence = 0.4

        if volume_trend:
            trend = volume_trend.lower()
            if trend == "increasing":
                score = 0.3
                return score, 0.6, "Rising volume confirms trend"
            elif trend == "decreasing":
                score = -0.2
                return score, 0.5, "Declining volume weakens trend"

        if volume_change is not None:
            if volume_change > 50:
                score = 0.4
                return score, 0.7, f"Volume surge +{volume_change:.0f}%"
            elif volume_change > 20:
                score = 0.2
            elif volume_change < -30:
                score = -0.2

        return score, confidence, ""

    def _analyze_trend(self, historical_data: Optional[List[Dict]]) -> tuple:
        """
        Analyze trend from historical data.

        Returns: (score, confidence, reasoning)
        """
        if not historical_data or len(historical_data) < 5:
            return 0.0, 0.0, ""

        # Get closing prices
        closes = [d.get("close") for d in historical_data if d.get("close")]

        if len(closes) < 5:
            return 0.0, 0.0, ""

        # Simple trend analysis - compare recent vs older prices
        recent = closes[-5:]
        older = closes[:5] if len(closes) >= 10 else closes[: len(closes) // 2]

        avg_recent = sum(recent) / len(recent)
        avg_older = sum(older) / len(older)

        if avg_older == 0:
            return 0.0, 0.0, ""

        trend_pct = ((avg_recent - avg_older) / avg_older) * 100

        # Calculate trend consistency (how many days moved in trend direction)
        if len(closes) >= 2:
            up_days = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i - 1])
            consistency = up_days / (len(closes) - 1)
        else:
            consistency = 0.5

        if trend_pct > 10:
            score = 0.5 + (consistency - 0.5) * 0.3
            return (
                min(score, 1.0),
                0.7,
                f"Uptrend +{trend_pct:.1f}% with {consistency * 100:.0f}% consistency",
            )
        elif trend_pct > 3:
            score = 0.2 + (consistency - 0.5) * 0.2
            return score, 0.5, f"Mild uptrend +{trend_pct:.1f}%"
        elif trend_pct < -10:
            score = -0.5 - (0.5 - consistency) * 0.3
            return max(score, -1.0), 0.7, f"Downtrend {trend_pct:.1f}%"
        elif trend_pct < -3:
            score = -0.2 - (0.5 - consistency) * 0.2
            return score, 0.5, f"Mild downtrend {trend_pct:.1f}%"

        return 0.0, 0.3, "Sideways consolidation"

    def _calculate_confidence(self, factors: Dict[str, float]) -> float:
        """
        Calculate overall confidence based on signal agreement.

        Returns: Confidence score (0.0 to 1.0)
        """
        non_zero = [f for f in factors.values() if abs(f) > 0.1]

        if len(non_zero) == 0:
            return 0.0

        # Check direction agreement
        positive = sum(1 for f in non_zero if f > 0)
        negative = len(non_zero) - positive

        # Agreement ratio
        if len(non_zero) > 0:
            agreement = max(positive, negative) / len(non_zero)
        else:
            agreement = 0.0

        # Data coverage (how many factors have data)
        coverage = len(non_zero) / len(factors) if factors else 0

        # Combined confidence
        confidence = agreement * 0.6 + coverage * 0.4

        return min(confidence, 1.0)

    def _analyze_sentiment(self, sentiment_data: Optional[Dict]) -> tuple:
        """
        Analyze sentiment data from Reddit and News sources.

        Args:
            sentiment_data: Combined sentiment data from SentimentDataService

        Returns: (score, confidence, reasoning)
        """
        if not sentiment_data:
            return 0.0, 0.0, ""

        # Extract combined sentiment score (-1 to 1)
        combined = sentiment_data.get("combined_sentiment", 0)
        total_mentions = sentiment_data.get("total_mentions", 0)
        sentiment_label = sentiment_data.get("sentiment_label", "neutral")

        # No data = no signal
        if total_mentions == 0:
            return 0.0, 0.0, ""

        # Calculate confidence based on data volume
        # More mentions = higher confidence in the signal
        if total_mentions < 5:
            confidence = 0.2
        elif total_mentions < 10:
            confidence = 0.3
        elif total_mentions < 25:
            confidence = 0.5
        elif total_mentions < 50:
            confidence = 0.6
        else:
            confidence = 0.7

        # Build reasoning
        reddit_score = sentiment_data.get("reddit", {}).get("sentiment_score", 0)
        news_score = sentiment_data.get("news", {}).get("sentiment_score", 0)

        reasoning_parts = [f"Sentiment: {sentiment_label}"]

        if reddit_score != 0:
            reddit_mentions = sentiment_data.get("reddit", {}).get("mentions", 0)
            reasoning_parts.append(f"Reddit({reddit_mentions}): {reddit_score:+.2f}")

        if news_score != 0:
            news_count = sentiment_data.get("news", {}).get("article_count", 0)
            reasoning_parts.append(f"News({news_count}): {news_score:+.2f}")

        reasoning = " | ".join(reasoning_parts)

        return combined, confidence, reasoning
