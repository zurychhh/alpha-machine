"""
Learning Engine
Calculates agent performance and optimizes weights with guardrails.

Core responsibilities:
1. Calculate rolling performance metrics (7d, 30d, 90d)
2. Propose new weights based on performance
3. Apply bias detection and correction via MetaLearningEngine
4. Enforce safety guardrails before applying changes
5. Log all changes to learning_log
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.models.agent_analysis import AgentAnalysis
from app.models.agent_weights_history import AgentWeightsHistory
from app.models.learning_log import LearningLog
from app.models.system_config import SystemConfig
from app.services.meta_learning_engine import (
    MetaLearningEngine,
    ProposedWeightChange,
    BiasDetectionResult,
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an agent over a time period."""
    win_rate: float
    trades_count: int
    total_pnl: float = 0.0
    avg_pnl_per_trade: float = 0.0


@dataclass
class RollingPerformance:
    """Rolling performance metrics for different time periods."""
    agent_name: str
    period_7d: PerformanceMetrics
    period_30d: PerformanceMetrics
    period_90d: PerformanceMetrics

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "7d": {
                "win_rate": self.period_7d.win_rate,
                "trades_count": self.period_7d.trades_count,
                "total_pnl": self.period_7d.total_pnl,
            },
            "30d": {
                "win_rate": self.period_30d.win_rate,
                "trades_count": self.period_30d.trades_count,
                "total_pnl": self.period_30d.total_pnl,
            },
            "90d": {
                "win_rate": self.period_90d.win_rate,
                "trades_count": self.period_90d.trades_count,
                "total_pnl": self.period_90d.total_pnl,
            },
        }


@dataclass
class OptimizationResult:
    """Result of the optimization process."""
    success: bool
    old_weights: Dict[str, float]
    new_weights: Dict[str, float]
    bias_report: Optional[BiasDetectionResult]
    guardrail_violations: List[str]
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "old_weights": self.old_weights,
            "new_weights": self.new_weights,
            "bias_report": self.bias_report.to_dict() if self.bias_report else None,
            "guardrail_violations": self.guardrail_violations,
            "reasoning": self.reasoning,
        }


class LearningEngine:
    """
    Main learning engine for agent weight optimization.

    Workflow:
    1. Calculate rolling performance for each agent
    2. Propose new weights based on weighted performance
    3. Detect and correct biases via MetaLearningEngine
    4. Check guardrails before applying
    5. Save results and log events
    """

    # Default agent names
    AGENT_NAMES = [
        "ContrarianAgent",
        "GrowthAgent",
        "MultiModalAgent",
        "PredictorAgent",
    ]

    # Default timeframe weights
    DEFAULT_TIMEFRAME_WEIGHTS = {"7d": 0.4, "30d": 0.4, "90d": 0.2}

    def __init__(self, db: Session):
        self.db = db
        self.meta_learning = MetaLearningEngine(db)
        self.logger = logging.getLogger("learning_engine")

    def get_config(self, key: str, default: str = None) -> Optional[str]:
        """Get configuration value from system_config."""
        config = (
            self.db.query(SystemConfig)
            .filter(SystemConfig.config_key == key)
            .first()
        )
        return config.config_value if config else default

    def get_config_float(self, key: str, default: float = 0.0) -> float:
        """Get float configuration value."""
        value = self.get_config(key)
        return float(value) if value else default

    def get_config_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value."""
        value = self.get_config(key)
        return value.lower() == "true" if value else default

    def get_timeframe_weights(self) -> Dict[str, float]:
        """Get timeframe weights from config."""
        value = self.get_config("LEARNING_TIMEFRAME_WEIGHTS")
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        return self.DEFAULT_TIMEFRAME_WEIGHTS

    def calculate_rolling_performance(
        self, agent_name: str, periods: List[int] = None
    ) -> RollingPerformance:
        """
        Calculate rolling performance for an agent over different time periods.

        Args:
            agent_name: Name of the agent
            periods: List of days to calculate (default: [7, 30, 90])

        Returns:
            RollingPerformance with metrics for each period
        """
        if periods is None:
            periods = [7, 30, 90]

        metrics = {}
        for days in periods:
            cutoff_date = datetime.now() - timedelta(days=days)
            metrics[days] = self._calculate_period_performance(agent_name, cutoff_date)

        return RollingPerformance(
            agent_name=agent_name,
            period_7d=metrics.get(7, PerformanceMetrics(0.0, 0)),
            period_30d=metrics.get(30, PerformanceMetrics(0.0, 0)),
            period_90d=metrics.get(90, PerformanceMetrics(0.0, 0)),
        )

    def _calculate_period_performance(
        self, agent_name: str, cutoff_date: datetime
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics for a specific period.

        A trade is considered a WIN if:
        - The agent recommended BUY and the signal resulted in positive P&L
        - The agent recommended SELL and the signal resulted in negative P&L
        - The signal status is CLOSED (actual outcome known)
        """
        # Get closed signals where this agent participated
        results = (
            self.db.query(
                AgentAnalysis.recommendation,
                Signal.pnl,
            )
            .join(Signal, AgentAnalysis.signal_id == Signal.id)
            .filter(
                AgentAnalysis.agent_name == agent_name,
                Signal.timestamp >= cutoff_date,
                Signal.status == "CLOSED",
                Signal.pnl.isnot(None),
            )
            .all()
        )

        if not results:
            return PerformanceMetrics(win_rate=0.0, trades_count=0)

        wins = 0
        total_pnl = 0.0

        for recommendation, pnl in results:
            pnl_value = float(pnl) if pnl else 0.0
            total_pnl += pnl_value

            # Determine if this was a correct recommendation
            if recommendation == "BUY" and pnl_value > 0:
                wins += 1
            elif recommendation == "SELL" and pnl_value < 0:
                wins += 1
            elif recommendation == "HOLD" and abs(pnl_value) < 5:
                # HOLD is correct if price didn't move much
                wins += 1

        trades_count = len(results)
        win_rate = (wins / trades_count * 100) if trades_count > 0 else 0.0
        avg_pnl = total_pnl / trades_count if trades_count > 0 else 0.0

        return PerformanceMetrics(
            win_rate=win_rate,
            trades_count=trades_count,
            total_pnl=total_pnl,
            avg_pnl_per_trade=avg_pnl,
        )

    def get_current_weights(self) -> Dict[str, float]:
        """Get current weights for all agents."""
        weights = {}

        for agent_name in self.AGENT_NAMES:
            latest = (
                self.db.query(AgentWeightsHistory)
                .filter(AgentWeightsHistory.agent_name == agent_name)
                .order_by(AgentWeightsHistory.date.desc())
                .first()
            )
            weights[agent_name] = float(latest.weight) if latest else 1.0

        return weights

    def calculate_new_weights(self) -> List[ProposedWeightChange]:
        """
        Calculate new weights based on rolling performance.

        Algorithm:
        1. For each agent: get rolling performance (7d, 30d, 90d)
        2. Calculate weighted_performance = 0.4×7d + 0.4×30d + 0.2×90d
        3. Calculate new_weight = 0.9×old_weight + 0.1×weighted_performance
        4. Apply bounds: clip(new_weight, 0.30, 2.00)
        5. Limit daily change: max 10% from old_weight
        """
        current_weights = self.get_current_weights()
        timeframe_weights = self.get_timeframe_weights()
        max_change = self.get_config_float("MAX_WEIGHT_CHANGE_DAILY", 0.10)
        min_bound = self.get_config_float("WEIGHT_MIN_BOUND", 0.30)
        max_bound = self.get_config_float("WEIGHT_MAX_BOUND", 2.00)

        proposed_changes = []

        for agent_name in self.AGENT_NAMES:
            perf = self.calculate_rolling_performance(agent_name)
            old_weight = current_weights.get(agent_name, 1.0)

            # Calculate weighted performance (as decimal 0-1)
            weighted_perf = (
                timeframe_weights["7d"] * (perf.period_7d.win_rate / 100.0)
                + timeframe_weights["30d"] * (perf.period_30d.win_rate / 100.0)
                + timeframe_weights["90d"] * (perf.period_90d.win_rate / 100.0)
            )

            # Convert to weight scale (0.5 win_rate = 1.0 weight)
            # 1.0 win_rate = 2.0 weight, 0.0 win_rate = 0.0 weight
            performance_weight = weighted_perf * 2

            # Blend with old weight (90% old, 10% new)
            new_weight = 0.9 * old_weight + 0.1 * performance_weight

            # Apply bounds
            new_weight = max(min_bound, min(max_bound, new_weight))

            # Limit daily change
            max_up = old_weight * (1 + max_change)
            max_down = old_weight * (1 - max_change)
            new_weight = max(max_down, min(max_up, new_weight))

            proposed_changes.append(
                ProposedWeightChange(
                    agent_name=agent_name,
                    old_weight=old_weight,
                    new_weight=round(new_weight, 3),
                    win_rate_7d=perf.period_7d.win_rate,
                    win_rate_30d=perf.period_30d.win_rate,
                    win_rate_90d=perf.period_90d.win_rate,
                    trades_count_7d=perf.period_7d.trades_count,
                    trades_count_30d=perf.period_30d.trades_count,
                    trades_count_90d=perf.period_90d.trades_count,
                )
            )

        # Normalize weights to sum to 4.0 (average of 1.0 per agent)
        total_weight = sum(c.new_weight for c in proposed_changes)
        if total_weight > 0:
            scale_factor = 4.0 / total_weight
            for c in proposed_changes:
                c.new_weight = round(c.new_weight * scale_factor, 3)

        return proposed_changes

    def is_safe_to_apply(
        self, proposed_changes: List[ProposedWeightChange]
    ) -> Tuple[bool, List[str]]:
        """
        Check if proposed changes pass all guardrails.

        Guardrails:
        1. No weight changed more than 20% in 7 days
        2. Sum of weights is approximately 4.0 (±10%)
        3. All weights within bounds [0.3, 2.0]

        Returns:
            Tuple of (is_safe, list of violations)
        """
        violations = []
        min_bound = self.get_config_float("WEIGHT_MIN_BOUND", 0.30)
        max_bound = self.get_config_float("WEIGHT_MAX_BOUND", 2.00)

        # Check 7-day cumulative change
        for change in proposed_changes:
            week_ago = date.today() - timedelta(days=7)
            history = (
                self.db.query(AgentWeightsHistory)
                .filter(
                    AgentWeightsHistory.agent_name == change.agent_name,
                    AgentWeightsHistory.date >= week_ago,
                )
                .order_by(AgentWeightsHistory.date.asc())
                .first()
            )

            if history:
                week_start_weight = float(history.weight)
                cumulative_change = abs(change.new_weight - week_start_weight) / week_start_weight
                if cumulative_change > 0.20:
                    violations.append(
                        f"{change.agent_name}: 7-day change {cumulative_change:.1%} > 20%"
                    )

        # Check weight sum
        total_weight = sum(c.new_weight for c in proposed_changes)
        if abs(total_weight - 4.0) > 0.4:  # ±10% of 4.0
            violations.append(f"Weight sum {total_weight:.2f} not within ±10% of 4.0")

        # Check individual bounds
        for change in proposed_changes:
            if change.new_weight < min_bound:
                violations.append(
                    f"{change.agent_name}: weight {change.new_weight:.2f} < min {min_bound}"
                )
            if change.new_weight > max_bound:
                violations.append(
                    f"{change.agent_name}: weight {change.new_weight:.2f} > max {max_bound}"
                )

        return len(violations) == 0, violations

    def optimize_daily(self) -> OptimizationResult:
        """
        Run daily weight optimization.

        Flow:
        1. Calculate new weights
        2. Detect biases via MetaLearningEngine
        3. If critical bias: apply corrections
        4. Check guardrails
        5. If safe: save changes
        6. Log everything
        """
        self.logger.info("Starting daily weight optimization")

        # Step 1: Calculate new weights
        proposed_changes = self.calculate_new_weights()
        old_weights = {c.agent_name: c.old_weight for c in proposed_changes}

        # Step 2: Detect biases
        bias_report = self.meta_learning.detect_learning_biases(proposed_changes)

        # Step 3: Apply corrections if needed
        if bias_report.has_critical_bias:
            self.logger.warning(f"Critical bias detected: {[b.type.value for b in bias_report.biases]}")
            proposed_changes = self.meta_learning.correct_biases(proposed_changes, bias_report)

        # Step 4: Check guardrails
        is_safe, violations = self.is_safe_to_apply(proposed_changes)

        new_weights = {c.agent_name: c.new_weight for c in proposed_changes}

        if not is_safe:
            self.logger.warning(f"Guardrail violations: {violations}")
            self._log_alert(violations, bias_report)
            return OptimizationResult(
                success=False,
                old_weights=old_weights,
                new_weights=new_weights,
                bias_report=bias_report,
                guardrail_violations=violations,
                reasoning=f"Blocked by guardrails: {'; '.join(violations)}",
            )

        # Step 5: Check if auto-learning is enabled or human review required
        auto_enabled = self.get_config_bool("AUTO_LEARNING_ENABLED", False)
        review_required = self.get_config_bool("HUMAN_REVIEW_REQUIRED", True)
        min_confidence = self.get_config_float("MIN_CONFIDENCE_FOR_AUTO", 0.80)

        if not auto_enabled or review_required:
            if bias_report.confidence < min_confidence:
                self._log_pending_review(proposed_changes, bias_report)
                return OptimizationResult(
                    success=False,
                    old_weights=old_weights,
                    new_weights=new_weights,
                    bias_report=bias_report,
                    guardrail_violations=[],
                    reasoning="Pending human review - confidence below threshold",
                )

        # Step 6: Apply changes
        self._save_weights(proposed_changes)
        self._log_weight_update(proposed_changes, bias_report)

        self.logger.info("Weight optimization completed successfully")

        return OptimizationResult(
            success=True,
            old_weights=old_weights,
            new_weights=new_weights,
            bias_report=bias_report,
            guardrail_violations=[],
            reasoning="Weights updated successfully",
        )

    def _save_weights(self, changes: List[ProposedWeightChange]) -> None:
        """Save new weights to database."""
        today = date.today()

        for change in changes:
            entry = AgentWeightsHistory(
                date=today,
                agent_name=change.agent_name,
                weight=Decimal(str(change.new_weight)),
                win_rate_7d=Decimal(str(change.win_rate_7d)) if change.win_rate_7d else None,
                win_rate_30d=Decimal(str(change.win_rate_30d)) if change.win_rate_30d else None,
                win_rate_90d=Decimal(str(change.win_rate_90d)) if change.win_rate_90d else None,
                trades_count_7d=change.trades_count_7d,
                trades_count_30d=change.trades_count_30d,
                trades_count_90d=change.trades_count_90d,
                reasoning=f"Auto-optimized: old={change.old_weight:.3f}, new={change.new_weight:.3f}",
            )
            self.db.add(entry)

        self.db.commit()

    def _log_weight_update(
        self, changes: List[ProposedWeightChange], bias_report: BiasDetectionResult
    ) -> None:
        """Log weight update event."""
        for change in changes:
            log_entry = LearningLog(
                date=date.today(),
                event_type="WEIGHT_UPDATE",
                agent_name=change.agent_name,
                metric_name="weight",
                old_value=Decimal(str(change.old_weight)),
                new_value=Decimal(str(change.new_weight)),
                reasoning=f"7d={change.win_rate_7d:.1f}%, 30d={change.win_rate_30d:.1f}%, 90d={change.win_rate_90d:.1f}%",
                confidence_level=Decimal(str(bias_report.confidence)),
            )
            self.db.add(log_entry)

        self.db.commit()

    def _log_alert(
        self, violations: List[str], bias_report: BiasDetectionResult
    ) -> None:
        """Log alert for blocked changes."""
        log_entry = LearningLog(
            date=date.today(),
            event_type="ALERT",
            reasoning=f"Guardrail violations: {'; '.join(violations)}",
            confidence_level=Decimal(str(bias_report.confidence)) if bias_report else None,
        )
        self.db.add(log_entry)
        self.db.commit()

    def _log_pending_review(
        self, changes: List[ProposedWeightChange], bias_report: BiasDetectionResult
    ) -> None:
        """Log pending human review event."""
        log_entry = LearningLog(
            date=date.today(),
            event_type="ALERT",
            reasoning=f"Pending human review - confidence {bias_report.confidence:.2f} < threshold",
            confidence_level=Decimal(str(bias_report.confidence)),
        )
        self.db.add(log_entry)
        self.db.commit()

    def manual_override(
        self, agent_name: str, new_weight: float, reasoning: str
    ) -> bool:
        """
        Manually override agent weight.

        Args:
            agent_name: Name of the agent
            new_weight: New weight value
            reasoning: Human-provided reasoning

        Returns:
            True if successful
        """
        if agent_name not in self.AGENT_NAMES:
            raise ValueError(f"Unknown agent: {agent_name}")

        min_bound = self.get_config_float("WEIGHT_MIN_BOUND", 0.30)
        max_bound = self.get_config_float("WEIGHT_MAX_BOUND", 2.00)

        if new_weight < min_bound or new_weight > max_bound:
            raise ValueError(f"Weight must be between {min_bound} and {max_bound}")

        current_weights = self.get_current_weights()
        old_weight = current_weights.get(agent_name, 1.0)

        # Save new weight
        entry = AgentWeightsHistory(
            date=date.today(),
            agent_name=agent_name,
            weight=Decimal(str(new_weight)),
            reasoning=f"Manual override: {reasoning}",
        )
        self.db.add(entry)

        # Log the override
        log_entry = LearningLog(
            date=date.today(),
            event_type="WEIGHT_UPDATE",
            agent_name=agent_name,
            metric_name="weight",
            old_value=Decimal(str(old_weight)),
            new_value=Decimal(str(new_weight)),
            reasoning=f"Manual override: {reasoning}",
            confidence_level=Decimal("1.0"),  # Human decision = full confidence
        )
        self.db.add(log_entry)

        self.db.commit()
        self.logger.info(f"Manual override: {agent_name} weight {old_weight} -> {new_weight}")

        return True

    def get_all_performance(self) -> List[RollingPerformance]:
        """Get rolling performance for all agents."""
        return [self.calculate_rolling_performance(name) for name in self.AGENT_NAMES]
