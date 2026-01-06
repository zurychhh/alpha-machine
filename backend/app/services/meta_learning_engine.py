"""
Meta-Learning Engine
Detects and corrects learning biases in the agent weight optimization system.

Implements 4 bias detectors:
1. OVERFITTING - When sample size is too small for statistical significance
2. RECENCY - When recent performance dominates over longer-term patterns
3. THRASHING - When weights oscillate rapidly without convergence
4. REGIME_BLINDNESS - When market regime changes are not accounted for
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.models.agent_weights_history import AgentWeightsHistory
from app.models.learning_log import LearningLog
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class BiasType(str, Enum):
    OVERFITTING = "OVERFITTING"
    RECENCY = "RECENCY"
    THRASHING = "THRASHING"
    REGIME_BLINDNESS = "REGIME_BLINDNESS"


class BiasSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MarketRegime(str, Enum):
    NORMAL = "NORMAL"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    BEAR_MARKET = "BEAR_MARKET"
    DIVERGENCE = "DIVERGENCE"


@dataclass
class BiasReport:
    """Individual bias detection result."""
    type: BiasType
    severity: BiasSeverity
    affected_agents: List[str]
    reasoning: str
    correction_needed: str


@dataclass
class BiasDetectionResult:
    """Complete bias detection analysis."""
    has_critical_bias: bool
    biases: List[BiasReport] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "has_critical_bias": self.has_critical_bias,
            "biases": [
                {
                    "type": b.type.value,
                    "severity": b.severity.value,
                    "affected_agents": b.affected_agents,
                    "reasoning": b.reasoning,
                    "correction_needed": b.correction_needed,
                }
                for b in self.biases
            ],
            "confidence": self.confidence,
        }


@dataclass
class ProposedWeightChange:
    """Proposed weight change for an agent."""
    agent_name: str
    old_weight: float
    new_weight: float
    win_rate_7d: Optional[float] = None
    win_rate_30d: Optional[float] = None
    win_rate_90d: Optional[float] = None
    trades_count_7d: int = 0
    trades_count_30d: int = 0
    trades_count_90d: int = 0


class MetaLearningEngine:
    """
    Detects and corrects learning biases in agent weight optimization.

    Uses 4 detection strategies:
    1. Overfitting Detector - Statistical significance check
    2. Recency Bias Neutralizer - Short vs long-term performance comparison
    3. Thrashing Prevention - Weight stability analysis
    4. Regime Change Detector - Market condition awareness
    """

    # Statistical thresholds
    MIN_TRADES_FOR_SIGNIFICANCE = 10
    CONFIDENCE_INTERVAL_THRESHOLD = 0.15
    RECENCY_DIFF_THRESHOLD = 0.20  # 20% difference between 7d and 30d
    THRASHING_STD_THRESHOLD = 0.30
    MAX_DIRECTION_REVERSALS = 3

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger("meta_learning")

    def detect_learning_biases(
        self,
        proposed_changes: List[ProposedWeightChange],
        historical_data: Optional[Dict[str, List[AgentWeightsHistory]]] = None,
    ) -> BiasDetectionResult:
        """
        Analyze proposed weight changes for learning biases.

        Args:
            proposed_changes: List of proposed weight changes per agent
            historical_data: Optional dict of agent_name -> weight history

        Returns:
            BiasDetectionResult with detected biases and correction recommendations
        """
        if historical_data is None:
            historical_data = self._get_historical_data()

        biases: List[BiasReport] = []

        # Run all 4 detectors
        overfitting_bias = self._detect_overfitting(proposed_changes)
        if overfitting_bias:
            biases.append(overfitting_bias)

        recency_bias = self._detect_recency_bias(proposed_changes)
        if recency_bias:
            biases.append(recency_bias)

        thrashing_bias = self._detect_thrashing(proposed_changes, historical_data)
        if thrashing_bias:
            biases.append(thrashing_bias)

        regime_bias = self._detect_regime_blindness(proposed_changes, historical_data)
        if regime_bias:
            biases.append(regime_bias)

        # Determine if any critical biases
        has_critical = any(b.severity == BiasSeverity.HIGH for b in biases)

        # Calculate overall confidence
        confidence = self._calculate_confidence(biases)

        return BiasDetectionResult(
            has_critical_bias=has_critical,
            biases=biases,
            confidence=confidence,
        )

    def correct_biases(
        self,
        proposed_changes: List[ProposedWeightChange],
        bias_report: BiasDetectionResult,
    ) -> List[ProposedWeightChange]:
        """
        Apply corrections for detected biases.

        Args:
            proposed_changes: Original proposed weight changes
            bias_report: Detected biases with correction recommendations

        Returns:
            Corrected weight changes
        """
        corrected = [
            ProposedWeightChange(
                agent_name=p.agent_name,
                old_weight=p.old_weight,
                new_weight=p.new_weight,
                win_rate_7d=p.win_rate_7d,
                win_rate_30d=p.win_rate_30d,
                win_rate_90d=p.win_rate_90d,
                trades_count_7d=p.trades_count_7d,
                trades_count_30d=p.trades_count_30d,
                trades_count_90d=p.trades_count_90d,
            )
            for p in proposed_changes
        ]

        for bias in bias_report.biases:
            if bias.type == BiasType.OVERFITTING:
                corrected = self._correct_overfitting(corrected, bias)
            elif bias.type == BiasType.RECENCY:
                corrected = self._correct_recency(corrected, bias)
            elif bias.type == BiasType.THRASHING:
                corrected = self._correct_thrashing(corrected, bias)
            elif bias.type == BiasType.REGIME_BLINDNESS:
                corrected = self._correct_regime(corrected, bias)

            # Log correction
            self._log_correction(bias)

        return corrected

    def _detect_overfitting(
        self, proposed_changes: List[ProposedWeightChange]
    ) -> Optional[BiasReport]:
        """
        Detect overfitting bias when sample size is too small.

        Calculates confidence interval: CI = 1.96 × sqrt((win_rate × (1-win_rate)) / N)
        If CI > 0.15, the result is not statistically significant.
        """
        affected_agents = []
        reasoning_parts = []

        for change in proposed_changes:
            # Check each time period
            for period, trades_count, win_rate in [
                ("7d", change.trades_count_7d, change.win_rate_7d),
                ("30d", change.trades_count_30d, change.win_rate_30d),
                ("90d", change.trades_count_90d, change.win_rate_90d),
            ]:
                if trades_count < self.MIN_TRADES_FOR_SIGNIFICANCE:
                    affected_agents.append(change.agent_name)
                    reasoning_parts.append(
                        f"{change.agent_name}: Only {trades_count} trades in {period}"
                    )
                    break

                if win_rate is not None and trades_count > 0:
                    wr = win_rate / 100.0  # Convert to decimal
                    ci = 1.96 * math.sqrt((wr * (1 - wr)) / trades_count)
                    if ci > self.CONFIDENCE_INTERVAL_THRESHOLD:
                        affected_agents.append(change.agent_name)
                        reasoning_parts.append(
                            f"{change.agent_name}: CI={ci:.2f} > {self.CONFIDENCE_INTERVAL_THRESHOLD} in {period}"
                        )
                        break

        if not affected_agents:
            return None

        # Remove duplicates
        affected_agents = list(set(affected_agents))

        severity = BiasSeverity.HIGH if len(affected_agents) >= 2 else BiasSeverity.MEDIUM

        return BiasReport(
            type=BiasType.OVERFITTING,
            severity=severity,
            affected_agents=affected_agents,
            reasoning=f"Statistically insignificant sample: {'; '.join(reasoning_parts)}",
            correction_needed="Reduce max_weight_change from 0.10 to 0.05 for affected agents",
        )

    def _detect_recency_bias(
        self, proposed_changes: List[ProposedWeightChange]
    ) -> Optional[BiasReport]:
        """
        Detect recency bias when short-term performance diverges significantly
        from longer-term performance.
        """
        affected_agents = []
        reasoning_parts = []

        for change in proposed_changes:
            if change.win_rate_7d is None or change.win_rate_30d is None:
                continue

            diff = abs(change.win_rate_7d - change.win_rate_30d) / 100.0

            if diff > self.RECENCY_DIFF_THRESHOLD:
                affected_agents.append(change.agent_name)
                direction = "spike" if change.win_rate_7d > change.win_rate_30d else "drop"
                reasoning_parts.append(
                    f"{change.agent_name}: 7d={change.win_rate_7d:.1f}% vs 30d={change.win_rate_30d:.1f}% ({direction})"
                )

        if not affected_agents:
            return None

        severity = BiasSeverity.HIGH if len(affected_agents) >= 2 else BiasSeverity.LOW

        return BiasReport(
            type=BiasType.RECENCY,
            severity=severity,
            affected_agents=affected_agents,
            reasoning=f"7d performance diverges from 30d: {'; '.join(reasoning_parts)}",
            correction_needed="Adjust timeframe weights: 7d=0.2, 30d=0.5, 90d=0.3",
        )

    def _detect_thrashing(
        self,
        proposed_changes: List[ProposedWeightChange],
        historical_data: Dict[str, List[AgentWeightsHistory]],
    ) -> Optional[BiasReport]:
        """
        Detect thrashing when weights oscillate rapidly without convergence.

        Checks:
        - Standard deviation of weight changes over 7 days
        - Number of direction reversals (up→down→up)
        """
        affected_agents = []
        reasoning_parts = []

        for change in proposed_changes:
            history = historical_data.get(change.agent_name, [])

            if len(history) < 3:
                continue

            # Get last 7 weight values
            recent_weights = [h.weight for h in history[:7]]

            if len(recent_weights) < 3:
                continue

            # Calculate standard deviation of changes
            changes = [
                float(recent_weights[i]) - float(recent_weights[i + 1])
                for i in range(len(recent_weights) - 1)
            ]

            if not changes:
                continue

            std_dev = self._std_dev(changes)

            # Count direction reversals
            reversals = 0
            for i in range(len(changes) - 1):
                if (changes[i] > 0 and changes[i + 1] < 0) or (
                    changes[i] < 0 and changes[i + 1] > 0
                ):
                    reversals += 1

            if std_dev > self.THRASHING_STD_THRESHOLD or reversals > self.MAX_DIRECTION_REVERSALS:
                affected_agents.append(change.agent_name)
                reasoning_parts.append(
                    f"{change.agent_name}: std={std_dev:.2f}, reversals={reversals}"
                )

        if not affected_agents:
            return None

        severity = BiasSeverity.HIGH  # Thrashing is always serious

        return BiasReport(
            type=BiasType.THRASHING,
            severity=severity,
            affected_agents=affected_agents,
            reasoning=f"Weight instability detected: {'; '.join(reasoning_parts)}",
            correction_needed="FREEZE weights for 3 days for affected agents",
        )

    def _detect_regime_blindness(
        self,
        proposed_changes: List[ProposedWeightChange],
        historical_data: Dict[str, List[AgentWeightsHistory]],
    ) -> Optional[BiasReport]:
        """
        Detect regime blindness when market conditions change but weights
        don't account for historical regime performance.
        """
        current_regime = self._get_current_regime()
        previous_regime = self._get_previous_regime()

        if current_regime == previous_regime:
            return None

        affected_agents = [c.agent_name for c in proposed_changes]

        return BiasReport(
            type=BiasType.REGIME_BLINDNESS,
            severity=BiasSeverity.MEDIUM,
            affected_agents=affected_agents,
            reasoning=f"Regime shift detected: {previous_regime.value} → {current_regime.value}",
            correction_needed="Blend weights: 70% new, 30% historical regime patterns",
        )

    def _correct_overfitting(
        self,
        changes: List[ProposedWeightChange],
        bias: BiasReport,
    ) -> List[ProposedWeightChange]:
        """Reduce weight change magnitude for overfitting agents."""
        max_change_reduced = 0.05  # Reduced from default 0.10

        for change in changes:
            if change.agent_name in bias.affected_agents:
                # Limit the weight change
                original_change = change.new_weight - change.old_weight
                if abs(original_change) > max_change_reduced:
                    sign = 1 if original_change > 0 else -1
                    change.new_weight = change.old_weight + (sign * max_change_reduced)

        return changes

    def _correct_recency(
        self,
        changes: List[ProposedWeightChange],
        bias: BiasReport,
    ) -> List[ProposedWeightChange]:
        """Recalculate weights with adjusted timeframe weights."""
        # New weights: 7d=0.2, 30d=0.5, 90d=0.3 (instead of 0.4, 0.4, 0.2)
        for change in changes:
            if change.agent_name in bias.affected_agents:
                if (
                    change.win_rate_7d is not None
                    and change.win_rate_30d is not None
                    and change.win_rate_90d is not None
                ):
                    # Recalculate with new weights
                    weighted_perf = (
                        0.2 * (change.win_rate_7d / 100.0)
                        + 0.5 * (change.win_rate_30d / 100.0)
                        + 0.3 * (change.win_rate_90d / 100.0)
                    )
                    # Blend with old weight
                    change.new_weight = 0.9 * change.old_weight + 0.1 * (weighted_perf * 2)

        return changes

    def _correct_thrashing(
        self,
        changes: List[ProposedWeightChange],
        bias: BiasReport,
    ) -> List[ProposedWeightChange]:
        """Freeze weights for thrashing agents."""
        for change in changes:
            if change.agent_name in bias.affected_agents:
                # Keep old weight (freeze)
                change.new_weight = change.old_weight

        return changes

    def _correct_regime(
        self,
        changes: List[ProposedWeightChange],
        bias: BiasReport,
    ) -> List[ProposedWeightChange]:
        """Blend new weights with historical regime patterns."""
        # 70% new, 30% old (conservative during regime change)
        for change in changes:
            if change.agent_name in bias.affected_agents:
                change.new_weight = 0.7 * change.new_weight + 0.3 * change.old_weight

        return changes

    def _get_historical_data(self) -> Dict[str, List[AgentWeightsHistory]]:
        """Get recent weight history for all agents."""
        cutoff_date = date.today() - timedelta(days=30)

        history = (
            self.db.query(AgentWeightsHistory)
            .filter(AgentWeightsHistory.date >= cutoff_date)
            .order_by(AgentWeightsHistory.date.desc())
            .all()
        )

        result: Dict[str, List[AgentWeightsHistory]] = {}
        for h in history:
            if h.agent_name not in result:
                result[h.agent_name] = []
            result[h.agent_name].append(h)

        return result

    def _get_current_regime(self) -> MarketRegime:
        """
        Determine current market regime.

        In a full implementation, this would:
        1. Fetch VIX from market data API
        2. Compare SPY price to SMA(200)
        3. Calculate AI sector correlation
        """
        # For now, return NORMAL - implement with real market data later
        return MarketRegime.NORMAL

    def _get_previous_regime(self) -> MarketRegime:
        """Get previous market regime from learning log."""
        log_entry = (
            self.db.query(LearningLog)
            .filter(LearningLog.event_type == "REGIME_SHIFT")
            .order_by(LearningLog.created_at.desc())
            .first()
        )

        if log_entry and log_entry.old_value:
            # Parse regime from old_value
            try:
                return MarketRegime(log_entry.metric_name)
            except ValueError:
                pass

        return MarketRegime.NORMAL

    def _calculate_confidence(self, biases: List[BiasReport]) -> float:
        """Calculate overall confidence in the learning update."""
        if not biases:
            return 1.0

        # Reduce confidence based on bias severity
        confidence = 1.0
        for bias in biases:
            if bias.severity == BiasSeverity.HIGH:
                confidence -= 0.3
            elif bias.severity == BiasSeverity.MEDIUM:
                confidence -= 0.15
            elif bias.severity == BiasSeverity.LOW:
                confidence -= 0.05

        return max(0.0, confidence)

    def _log_correction(self, bias: BiasReport) -> None:
        """Log bias correction to learning_log."""
        log_entry = LearningLog(
            date=date.today(),
            event_type="CORRECTION_APPLIED",
            agent_name=", ".join(bias.affected_agents),
            reasoning=bias.reasoning,
            bias_type=bias.type.value,
            correction_applied=bias.correction_needed,
        )
        self.db.add(log_entry)
        self.db.commit()

    @staticmethod
    def _std_dev(values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
