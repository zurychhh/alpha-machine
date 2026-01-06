"""
Regime Detector
Detects current market regime to adjust learning behavior.

Market Regimes:
1. NORMAL - Standard market conditions
2. HIGH_VOLATILITY - VIX > 25
3. BEAR_MARKET - SPY below SMA(200)
4. DIVERGENCE - AI sector decoupled from broad market
"""

import logging
from datetime import date, datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.models.learning_log import LearningLog
from app.models.market_data import MarketData
from app.services.market_data import MarketDataService

logger = logging.getLogger(__name__)


class MarketRegime(str, Enum):
    """Market regime classifications."""
    NORMAL = "NORMAL"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    BEAR_MARKET = "BEAR_MARKET"
    DIVERGENCE = "DIVERGENCE"


@dataclass
class RegimeAnalysis:
    """Result of regime detection analysis."""
    current_regime: MarketRegime
    previous_regime: Optional[MarketRegime]
    regime_changed: bool
    vix_level: Optional[float]
    spy_vs_sma200: Optional[float]  # % above/below SMA(200)
    ai_sector_correlation: Optional[float]
    confidence: float
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_regime": self.current_regime.value,
            "previous_regime": self.previous_regime.value if self.previous_regime else None,
            "regime_changed": self.regime_changed,
            "vix_level": self.vix_level,
            "spy_vs_sma200": self.spy_vs_sma200,
            "ai_sector_correlation": self.ai_sector_correlation,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }


class RegimeDetector:
    """
    Detects current market regime based on multiple signals.

    Uses:
    - VIX level (volatility indicator)
    - SPY price vs SMA(200) (trend indicator)
    - AI sector correlation with SPY (sector divergence)
    """

    # Thresholds
    VIX_HIGH_THRESHOLD = 25.0  # VIX above this = HIGH_VOLATILITY
    VIX_EXTREME_THRESHOLD = 35.0  # VIX above this = extreme fear
    SMA_BEAR_THRESHOLD = -0.05  # SPY 5% below SMA(200) = BEAR_MARKET
    CORRELATION_DIVERGENCE_THRESHOLD = 0.3  # Low correlation = DIVERGENCE

    def __init__(self, db: Session):
        self.db = db
        self.market_data_service = MarketDataService()
        self.logger = logging.getLogger("regime_detector")

    def detect_current_regime(self) -> RegimeAnalysis:
        """
        Detect the current market regime.

        Returns:
            RegimeAnalysis with current regime and supporting data
        """
        # Get market indicators
        vix_level = self._get_vix_level()
        spy_vs_sma = self._get_spy_vs_sma200()
        ai_correlation = self._get_ai_sector_correlation()

        # Determine regime based on priority
        # 1. HIGH_VOLATILITY takes precedence if VIX is extreme
        # 2. BEAR_MARKET if significantly below SMA(200)
        # 3. DIVERGENCE if AI sector uncorrelated
        # 4. NORMAL otherwise

        reasoning_parts = []
        current_regime = MarketRegime.NORMAL
        confidence = 0.8

        # Check VIX first (highest priority during crises)
        if vix_level is not None:
            if vix_level >= self.VIX_EXTREME_THRESHOLD:
                current_regime = MarketRegime.HIGH_VOLATILITY
                confidence = 0.95
                reasoning_parts.append(f"VIX at {vix_level:.1f} (extreme fear)")
            elif vix_level >= self.VIX_HIGH_THRESHOLD:
                current_regime = MarketRegime.HIGH_VOLATILITY
                confidence = 0.85
                reasoning_parts.append(f"VIX at {vix_level:.1f} (elevated)")

        # Check SPY trend (bear market overrides normal but not volatility)
        if spy_vs_sma is not None and current_regime == MarketRegime.NORMAL:
            if spy_vs_sma <= self.SMA_BEAR_THRESHOLD:
                current_regime = MarketRegime.BEAR_MARKET
                confidence = 0.85
                reasoning_parts.append(
                    f"SPY {spy_vs_sma*100:.1f}% below SMA(200)"
                )

        # Check AI sector correlation (divergence is informational)
        if ai_correlation is not None and current_regime == MarketRegime.NORMAL:
            if ai_correlation < self.CORRELATION_DIVERGENCE_THRESHOLD:
                current_regime = MarketRegime.DIVERGENCE
                confidence = 0.75
                reasoning_parts.append(
                    f"AI sector correlation {ai_correlation:.2f} (decoupled)"
                )

        # Get previous regime
        previous_regime = self._get_previous_regime()
        regime_changed = previous_regime != current_regime if previous_regime else False

        # Build reasoning
        if not reasoning_parts:
            reasoning_parts.append("Normal market conditions")

        if regime_changed and previous_regime:
            reasoning_parts.append(f"Regime shift from {previous_regime.value}")

        # Log regime shift
        if regime_changed:
            self._log_regime_shift(previous_regime, current_regime, reasoning_parts)

        return RegimeAnalysis(
            current_regime=current_regime,
            previous_regime=previous_regime,
            regime_changed=regime_changed,
            vix_level=vix_level,
            spy_vs_sma200=spy_vs_sma,
            ai_sector_correlation=ai_correlation,
            confidence=confidence,
            reasoning="; ".join(reasoning_parts),
        )

    def _get_vix_level(self) -> Optional[float]:
        """Get current VIX level from market data."""
        try:
            # Try to get VIX from market data service
            vix_data = self.market_data_service.get_current_price("^VIX")
            if vix_data and "price" in vix_data:
                return float(vix_data["price"])
        except Exception as e:
            self.logger.warning(f"Failed to get VIX level: {e}")

        # Fallback: check database for recent VIX data
        try:
            recent = (
                self.db.query(MarketData)
                .filter(MarketData.ticker == "^VIX")
                .order_by(MarketData.date.desc())
                .first()
            )
            if recent and recent.close:
                return float(recent.close)
        except Exception as e:
            self.logger.warning(f"Failed to get VIX from database: {e}")

        return None

    def _get_spy_vs_sma200(self) -> Optional[float]:
        """
        Calculate SPY price relative to its 200-day SMA.

        Returns:
            Percentage above/below SMA(200), e.g., -0.05 means 5% below
        """
        try:
            # Get historical SPY data (need 200 days for SMA)
            history = self.market_data_service.get_historical_data(
                "SPY", period="1y"
            )
            if not history or len(history) < 200:
                return None

            # Calculate SMA(200)
            closes = [float(h.get("close", 0)) for h in history[-200:]]
            sma_200 = sum(closes) / len(closes)

            # Get current price
            current_price = float(history[-1].get("close", 0))

            if sma_200 > 0:
                return (current_price - sma_200) / sma_200

        except Exception as e:
            self.logger.warning(f"Failed to calculate SPY vs SMA(200): {e}")

        return None

    def _get_ai_sector_correlation(self) -> Optional[float]:
        """
        Calculate correlation between AI sector and SPY over last 30 days.

        Uses top AI stocks (NVDA, MSFT, GOOGL) as proxy for AI sector.

        Returns:
            Correlation coefficient (0-1)
        """
        try:
            ai_tickers = ["NVDA", "MSFT", "GOOGL"]
            spy_history = self.market_data_service.get_historical_data(
                "SPY", period="1mo"
            )
            if not spy_history or len(spy_history) < 20:
                return None

            spy_returns = self._calculate_returns(spy_history)

            correlations = []
            for ticker in ai_tickers:
                ticker_history = self.market_data_service.get_historical_data(
                    ticker, period="1mo"
                )
                if ticker_history and len(ticker_history) >= 20:
                    ticker_returns = self._calculate_returns(ticker_history)
                    corr = self._calculate_correlation(spy_returns, ticker_returns)
                    if corr is not None:
                        correlations.append(corr)

            if correlations:
                return sum(correlations) / len(correlations)

        except Exception as e:
            self.logger.warning(f"Failed to calculate AI sector correlation: {e}")

        return None

    def _calculate_returns(self, history: List[Dict]) -> List[float]:
        """Calculate daily returns from price history."""
        returns = []
        for i in range(1, len(history)):
            prev_close = float(history[i-1].get("close", 0))
            curr_close = float(history[i].get("close", 0))
            if prev_close > 0:
                returns.append((curr_close - prev_close) / prev_close)
        return returns

    def _calculate_correlation(
        self, returns1: List[float], returns2: List[float]
    ) -> Optional[float]:
        """Calculate Pearson correlation between two return series."""
        n = min(len(returns1), len(returns2))
        if n < 10:
            return None

        r1 = returns1[-n:]
        r2 = returns2[-n:]

        mean1 = sum(r1) / n
        mean2 = sum(r2) / n

        numerator = sum((r1[i] - mean1) * (r2[i] - mean2) for i in range(n))
        denom1 = sum((x - mean1) ** 2 for x in r1) ** 0.5
        denom2 = sum((x - mean2) ** 2 for x in r2) ** 0.5

        if denom1 > 0 and denom2 > 0:
            return numerator / (denom1 * denom2)

        return None

    def _get_previous_regime(self) -> Optional[MarketRegime]:
        """Get the most recently recorded regime from learning_log."""
        try:
            log_entry = (
                self.db.query(LearningLog)
                .filter(LearningLog.event_type == "REGIME_SHIFT")
                .order_by(LearningLog.created_at.desc())
                .first()
            )

            if log_entry and log_entry.metric_name:
                try:
                    return MarketRegime(log_entry.metric_name)
                except ValueError:
                    pass
        except Exception as e:
            self.logger.warning(f"Failed to get previous regime: {e}")

        return None

    def _log_regime_shift(
        self,
        old_regime: Optional[MarketRegime],
        new_regime: MarketRegime,
        reasoning_parts: List[str],
    ) -> None:
        """Log regime shift to learning_log."""
        try:
            log_entry = LearningLog(
                date=date.today(),
                event_type="REGIME_SHIFT",
                metric_name=new_regime.value,
                reasoning=f"Regime shift: {old_regime.value if old_regime else 'UNKNOWN'} -> {new_regime.value}. {'; '.join(reasoning_parts)}",
            )
            self.db.add(log_entry)
            self.db.commit()

            self.logger.info(
                f"Regime shift detected: {old_regime} -> {new_regime}"
            )
        except Exception as e:
            self.logger.error(f"Failed to log regime shift: {e}")

    def get_regime_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get regime shift history for the past N days.

        Returns:
            List of regime shift events
        """
        cutoff = date.today() - timedelta(days=days)

        logs = (
            self.db.query(LearningLog)
            .filter(
                LearningLog.event_type == "REGIME_SHIFT",
                LearningLog.date >= cutoff,
            )
            .order_by(LearningLog.created_at.desc())
            .all()
        )

        return [log.to_dict() for log in logs]

    def should_freeze_learning(self) -> bool:
        """
        Determine if learning should be frozen due to regime uncertainty.

        Freeze if:
        - Multiple regime shifts in last 7 days
        - Currently in HIGH_VOLATILITY with extreme VIX

        Returns:
            True if learning should be frozen
        """
        # Check for multiple regime shifts
        week_ago = date.today() - timedelta(days=7)
        recent_shifts = (
            self.db.query(LearningLog)
            .filter(
                LearningLog.event_type == "REGIME_SHIFT",
                LearningLog.date >= week_ago,
            )
            .count()
        )

        if recent_shifts >= 3:
            return True

        # Check for extreme volatility
        current = self.detect_current_regime()
        if (
            current.current_regime == MarketRegime.HIGH_VOLATILITY
            and current.vix_level
            and current.vix_level >= self.VIX_EXTREME_THRESHOLD
        ):
            return True

        return False
