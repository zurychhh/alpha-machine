"""
Signal Ranking System - sorts signals by quality composite score.

Used by the backtesting engine to prioritize which signals to allocate capital to.
"""

from typing import List, Dict
from sqlalchemy.orm import Session
import logging

from app.models.signal import Signal

logger = logging.getLogger(__name__)


class SignalRanker:
    """Ranks signals based on composite score for portfolio allocation."""

    def rank_signals(self, signals: List[Signal], db: Session) -> List[Dict]:
        """
        Rank signals by composite quality score.

        Score formula: confidence × expected_return × (1 / risk_factor)

        Higher score = better signal quality for portfolio allocation.

        Args:
            signals: List of Signal objects from database
            db: Database session (for potential future lookups)

        Returns:
            List of dicts with ranked signals:
            [
                {
                    "signal": Signal object,
                    "score": 0.85,
                    "rank": 1,
                    "expected_return": 0.15,
                    "risk_factor": 1.2,
                    "confidence": 4
                },
                ...
            ]
        """
        ranked = []

        for signal in signals:
            # Only rank BUY signals (we want to allocate capital to buys)
            if signal.signal_type != "BUY":
                continue

            # Calculate expected return (from entry to target)
            expected_return = self._calculate_expected_return(signal)

            # Calculate risk factor (based on stop-loss distance)
            risk_factor = self._calculate_risk_factor(signal)

            # Composite score: higher confidence, higher return, lower risk = better
            # Normalize confidence from 1-5 scale to 0-1
            confidence_norm = float(signal.confidence) / 5.0
            score = confidence_norm * expected_return * (1.0 / risk_factor)

            ranked.append(
                {
                    "signal": signal,
                    "score": round(score, 6),
                    "expected_return": round(expected_return, 4),
                    "risk_factor": round(risk_factor, 2),
                    "confidence": signal.confidence,
                }
            )

        # Sort by score descending (best signals first)
        ranked.sort(key=lambda x: x["score"], reverse=True)

        # Add rank position
        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        logger.info(f"Ranked {len(ranked)} BUY signals out of {len(signals)} total signals")
        return ranked

    def _calculate_expected_return(self, signal: Signal) -> float:
        """
        Calculate expected return percentage from entry to target.

        Args:
            signal: Signal with entry_price and target_price

        Returns:
            Expected return as decimal (e.g., 0.25 = 25% return)
        """
        if signal.entry_price and signal.target_price:
            entry = float(signal.entry_price)
            target = float(signal.target_price)
            if entry > 0:
                return (target - entry) / entry

        # Default 10% expected return if prices not set
        return 0.10

    def _calculate_risk_factor(self, signal: Signal) -> float:
        """
        Calculate risk factor based on stop-loss distance.

        Larger stop-loss distance = higher risk factor.

        Args:
            signal: Signal with entry_price and stop_loss

        Returns:
            Risk factor multiplier (1.0 = baseline, higher = riskier)
        """
        if signal.entry_price and signal.stop_loss:
            entry = float(signal.entry_price)
            stop = float(signal.stop_loss)
            if entry > 0:
                downside_risk = (entry - stop) / entry
                # Scale: 10% downside = risk factor 1.0
                # 20% downside = risk factor 2.0, etc.
                return max(1.0, downside_risk * 10)

        # Default medium risk if stop-loss not set
        return 1.5

    def get_top_signals(
        self, signals: List[Signal], db: Session, top_n: int = 5
    ) -> List[Dict]:
        """
        Get top N ranked signals.

        Convenience method for quickly getting best signals.

        Args:
            signals: List of Signal objects
            db: Database session
            top_n: Number of top signals to return

        Returns:
            Top N ranked signals
        """
        ranked = self.rank_signals(signals, db)
        return ranked[:top_n]


# Singleton instance
signal_ranker = SignalRanker()
