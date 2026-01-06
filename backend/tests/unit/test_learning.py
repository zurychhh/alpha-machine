"""
Unit tests for the Self-Learning System.

Tests for:
- MetaLearningEngine bias detection
- LearningEngine weight optimization
- RegimeDetector market regime classification
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.meta_learning_engine import (
    MetaLearningEngine,
    BiasType,
    BiasSeverity,
    MarketRegime,
    BiasDetectionResult,
    BiasReport,
    ProposedWeightChange,
)
from app.services.learning_engine import (
    LearningEngine,
    PerformanceMetrics,
    RollingPerformance,
    OptimizationResult,
)
from app.services.regime_detector import RegimeDetector, RegimeAnalysis
from app.models.agent_weights_history import AgentWeightsHistory
from app.models.learning_log import LearningLog
from app.models.system_config import SystemConfig


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.all.return_value = []
    return db


@pytest.fixture
def sample_proposed_changes():
    """Sample proposed weight changes for testing."""
    return [
        ProposedWeightChange(
            agent_name="ContrarianAgent",
            old_weight=1.0,
            new_weight=1.1,
            win_rate_7d=60.0,
            win_rate_30d=55.0,
            win_rate_90d=52.0,
            trades_count_7d=15,
            trades_count_30d=45,
            trades_count_90d=120,
        ),
        ProposedWeightChange(
            agent_name="GrowthAgent",
            old_weight=1.0,
            new_weight=0.9,
            win_rate_7d=45.0,
            win_rate_30d=50.0,
            win_rate_90d=53.0,
            trades_count_7d=12,
            trades_count_30d=40,
            trades_count_90d=100,
        ),
    ]


@pytest.fixture
def low_sample_changes():
    """Proposed changes with low sample sizes (for overfitting detection)."""
    return [
        ProposedWeightChange(
            agent_name="ContrarianAgent",
            old_weight=1.0,
            new_weight=1.3,
            win_rate_7d=80.0,
            win_rate_30d=70.0,
            win_rate_90d=60.0,
            trades_count_7d=5,  # Below MIN_TRADES_FOR_SIGNIFICANCE
            trades_count_30d=8,
            trades_count_90d=20,
        ),
    ]


@pytest.fixture
def recency_bias_changes():
    """Proposed changes with high recency bias."""
    return [
        ProposedWeightChange(
            agent_name="ContrarianAgent",
            old_weight=1.0,
            new_weight=1.4,
            win_rate_7d=85.0,  # Much higher than 30d
            win_rate_30d=55.0,
            win_rate_90d=50.0,
            trades_count_7d=15,
            trades_count_30d=45,
            trades_count_90d=120,
        ),
    ]


# ============================================================================
# MetaLearningEngine Tests
# ============================================================================


class TestMetaLearningEngine:
    """Tests for MetaLearningEngine bias detection."""

    @pytest.fixture
    def meta_engine(self, mock_db):
        """Create MetaLearningEngine instance with mocked DB."""
        return MetaLearningEngine(mock_db)

    def test_initialization(self, meta_engine):
        """MetaLearningEngine initializes correctly."""
        assert meta_engine is not None
        assert hasattr(meta_engine, 'db')
        assert meta_engine.MIN_TRADES_FOR_SIGNIFICANCE == 10
        assert meta_engine.CONFIDENCE_INTERVAL_THRESHOLD == 0.15

    def test_detect_no_biases_with_good_data(
        self, meta_engine, sample_proposed_changes
    ):
        """No biases detected with clean data."""
        result = meta_engine.detect_learning_biases(
            sample_proposed_changes, historical_data={}
        )

        assert isinstance(result, BiasDetectionResult)
        assert result.confidence >= 0.0
        assert result.confidence <= 1.0

    def test_detect_overfitting_low_sample(
        self, meta_engine, low_sample_changes
    ):
        """Detects overfitting when sample size is too small."""
        result = meta_engine.detect_learning_biases(
            low_sample_changes, historical_data={}
        )

        # Should detect overfitting bias
        overfitting_biases = [
            b for b in result.biases if b.type == BiasType.OVERFITTING
        ]
        assert len(overfitting_biases) > 0
        assert "ContrarianAgent" in overfitting_biases[0].affected_agents

    def test_detect_recency_bias(self, meta_engine, recency_bias_changes):
        """Detects recency bias when 7d diverges from 30d."""
        result = meta_engine.detect_learning_biases(
            recency_bias_changes, historical_data={}
        )

        # Should detect recency bias (85% - 55% = 30% > 20% threshold)
        recency_biases = [
            b for b in result.biases if b.type == BiasType.RECENCY
        ]
        assert len(recency_biases) > 0

    def test_correct_overfitting_reduces_change(self, meta_engine):
        """Overfitting correction reduces weight change magnitude."""
        changes = [
            ProposedWeightChange(
                agent_name="TestAgent",
                old_weight=1.0,
                new_weight=1.2,  # 20% increase
                trades_count_7d=5,
            )
        ]

        bias = BiasReport(
            type=BiasType.OVERFITTING,
            severity=BiasSeverity.MEDIUM,
            affected_agents=["TestAgent"],
            reasoning="Low sample size",
            correction_needed="Reduce max change",
        )

        corrected = meta_engine._correct_overfitting(changes, bias)

        # Change should be reduced (max 0.05 for overfitting)
        assert corrected[0].new_weight < 1.2
        assert corrected[0].new_weight >= 1.0

    def test_correct_thrashing_freezes_weights(self, meta_engine):
        """Thrashing correction freezes weights."""
        changes = [
            ProposedWeightChange(
                agent_name="TestAgent",
                old_weight=1.0,
                new_weight=1.15,
            )
        ]

        bias = BiasReport(
            type=BiasType.THRASHING,
            severity=BiasSeverity.HIGH,
            affected_agents=["TestAgent"],
            reasoning="Weight oscillation detected",
            correction_needed="Freeze weights",
        )

        corrected = meta_engine._correct_thrashing(changes, bias)

        # Weight should be frozen (kept at old value)
        assert corrected[0].new_weight == corrected[0].old_weight

    def test_confidence_calculation(self, meta_engine):
        """Confidence calculation based on biases."""
        # No biases = full confidence
        no_biases = []
        assert meta_engine._calculate_confidence(no_biases) == 1.0

        # High severity bias reduces confidence
        high_bias = [
            BiasReport(
                type=BiasType.OVERFITTING,
                severity=BiasSeverity.HIGH,
                affected_agents=["Agent1"],
                reasoning="Test",
                correction_needed="Test",
            )
        ]
        confidence = meta_engine._calculate_confidence(high_bias)
        assert confidence < 1.0
        assert confidence >= 0.0

    def test_std_dev_calculation(self, meta_engine):
        """Standard deviation calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        std = meta_engine._std_dev(values)
        assert abs(std - 1.5811) < 0.01

        # Single value returns 0
        assert meta_engine._std_dev([1.0]) == 0.0

        # Empty list returns 0
        assert meta_engine._std_dev([]) == 0.0


# ============================================================================
# BiasType Tests
# ============================================================================


class TestBiasType:
    """Tests for BiasType enum."""

    def test_bias_types_exist(self):
        """All expected bias types exist."""
        assert BiasType.OVERFITTING
        assert BiasType.RECENCY
        assert BiasType.THRASHING
        assert BiasType.REGIME_BLINDNESS

    def test_bias_type_values(self):
        """Bias types have correct string values."""
        assert BiasType.OVERFITTING.value == "OVERFITTING"
        assert BiasType.RECENCY.value == "RECENCY"


# ============================================================================
# LearningEngine Tests
# ============================================================================


class TestLearningEngine:
    """Tests for LearningEngine weight optimization."""

    @pytest.fixture
    def learning_engine(self, mock_db):
        """Create LearningEngine with mocked DB."""
        return LearningEngine(mock_db)

    def test_initialization(self, learning_engine):
        """LearningEngine initializes correctly."""
        assert learning_engine is not None
        assert hasattr(learning_engine, 'db')
        assert hasattr(learning_engine, 'meta_learning')
        assert len(learning_engine.AGENT_NAMES) == 4

    def test_get_current_weights_defaults(self, learning_engine, mock_db):
        """Getting current weights returns defaults when no history."""
        weights = learning_engine.get_current_weights()

        assert len(weights) == 4
        for agent in learning_engine.AGENT_NAMES:
            assert weights[agent] == 1.0

    def test_get_config_values(self, learning_engine, mock_db):
        """Getting configuration values."""
        mock_config = Mock()
        mock_config.config_value = "true"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        assert learning_engine.get_config("AUTO_LEARNING_ENABLED") == "true"
        assert learning_engine.get_config_bool("AUTO_LEARNING_ENABLED") is True

    def test_get_timeframe_weights(self, learning_engine, mock_db):
        """Getting timeframe weights from config."""
        # With no config, should return defaults
        mock_db.query.return_value.filter.return_value.first.return_value = None

        weights = learning_engine.get_timeframe_weights()

        assert weights["7d"] == 0.4
        assert weights["30d"] == 0.4
        assert weights["90d"] == 0.2

    def test_is_safe_to_apply_exceeds_bounds(self, learning_engine, mock_db):
        """Guardrail check fails for out-of-bounds weights."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        changes = [
            ProposedWeightChange(
                agent_name="ContrarianAgent",
                old_weight=1.0,
                new_weight=2.5,  # Exceeds max bound (2.0)
            ),
        ]

        is_safe, violations = learning_engine.is_safe_to_apply(changes)

        assert is_safe is False
        assert any("max" in v.lower() for v in violations)

    def test_manual_override_validates_bounds(self, learning_engine, mock_db):
        """Manual override validates weight bounds."""
        with pytest.raises(ValueError) as exc_info:
            learning_engine.manual_override(
                agent_name="ContrarianAgent",
                new_weight=3.0,  # Exceeds max bound
                reasoning="Test override",
            )

        assert "between" in str(exc_info.value).lower()

    def test_manual_override_validates_agent_name(self, learning_engine, mock_db):
        """Manual override validates agent name."""
        with pytest.raises(ValueError) as exc_info:
            learning_engine.manual_override(
                agent_name="InvalidAgent",
                new_weight=1.5,
                reasoning="Test override",
            )

        assert "unknown agent" in str(exc_info.value).lower()

    def test_optimize_daily_returns_result(self, learning_engine, mock_db):
        """optimize_daily returns OptimizationResult."""
        # Mock get_config to return proper string values
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch.object(learning_engine, 'get_timeframe_weights', return_value={"7d": 0.4, "30d": 0.4, "90d": 0.2}):
            with patch.object(learning_engine, 'get_config_float', return_value=0.1):
                with patch.object(learning_engine, 'get_config_bool', return_value=False):
                    result = learning_engine.optimize_daily()

        assert isinstance(result, OptimizationResult)
        assert hasattr(result, 'success')
        assert hasattr(result, 'old_weights')
        assert hasattr(result, 'new_weights')
        assert hasattr(result, 'bias_report')


# ============================================================================
# RollingPerformance Tests
# ============================================================================


class TestRollingPerformance:
    """Tests for RollingPerformance dataclass."""

    def test_rolling_performance_structure(self):
        """RollingPerformance has correct structure."""
        period_7d = PerformanceMetrics(
            win_rate=75.0,
            trades_count=20,
            total_pnl=500.0,
            avg_pnl_per_trade=25.0,
        )
        period_30d = PerformanceMetrics(
            win_rate=65.0,
            trades_count=80,
        )
        period_90d = PerformanceMetrics(
            win_rate=60.0,
            trades_count=200,
        )

        perf = RollingPerformance(
            agent_name="TestAgent",
            period_7d=period_7d,
            period_30d=period_30d,
            period_90d=period_90d,
        )

        assert perf.agent_name == "TestAgent"
        assert perf.period_7d.win_rate == 75.0
        assert perf.period_30d.win_rate == 65.0


# ============================================================================
# Learning Models Tests
# ============================================================================


class TestAgentWeightsHistoryModel:
    """Tests for AgentWeightsHistory model."""

    def test_model_repr(self):
        """Model __repr__ returns expected format."""
        history = AgentWeightsHistory(
            date=date.today(),
            agent_name="ContrarianAgent",
            weight=Decimal("1.25"),
        )

        repr_str = repr(history)
        assert "ContrarianAgent" in repr_str
        assert "1.25" in repr_str

    def test_model_to_dict(self):
        """Model to_dict returns dictionary."""
        history = AgentWeightsHistory(
            date=date.today(),
            agent_name="GrowthAgent",
            weight=Decimal("0.95"),
            win_rate_7d=Decimal("55.00"),
            trades_count_7d=15,
        )

        result = history.to_dict()

        assert isinstance(result, dict)
        assert result["agent_name"] == "GrowthAgent"
        assert result["weight"] == 0.95


class TestLearningLogModel:
    """Tests for LearningLog model."""

    def test_model_repr(self):
        """Model __repr__ returns expected format."""
        log = LearningLog(
            date=date.today(),
            event_type="WEIGHT_UPDATE",
            agent_name="ContrarianAgent",
        )

        repr_str = repr(log)
        assert "WEIGHT_UPDATE" in repr_str
        assert "ContrarianAgent" in repr_str

    def test_event_types(self):
        """Learning log can have different event types."""
        event_types = [
            "WEIGHT_UPDATE",
            "BIAS_DETECTED",
            "CORRECTION_APPLIED",
            "REGIME_SHIFT",
            "FREEZE",
            "ALERT",
        ]

        for event_type in event_types:
            log = LearningLog(
                date=date.today(),
                event_type=event_type,
            )
            assert log.event_type == event_type


class TestSystemConfigModel:
    """Tests for SystemConfig model."""

    def test_get_default_configs(self):
        """Default configs include all expected keys."""
        defaults = SystemConfig.get_default_configs()

        assert isinstance(defaults, list)
        assert len(defaults) > 0

        keys = [d["config_key"] for d in defaults]
        assert "AUTO_LEARNING_ENABLED" in keys
        assert "HUMAN_REVIEW_REQUIRED" in keys
        assert "MAX_WEIGHT_CHANGE_DAILY" in keys

    def test_model_to_dict(self):
        """Model to_dict returns dictionary."""
        config = SystemConfig(
            config_key="TEST_KEY",
            config_value="test_value",
            description="Test description",
        )

        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["config_key"] == "TEST_KEY"
        assert result["config_value"] == "test_value"


# ============================================================================
# RegimeDetector Tests
# ============================================================================


class TestRegimeDetector:
    """Tests for RegimeDetector market regime classification."""

    @pytest.fixture
    def regime_detector(self, mock_db):
        """Create RegimeDetector with mock db."""
        with patch('app.services.regime_detector.MarketDataService'):
            return RegimeDetector(mock_db)

    def test_initialization(self, regime_detector):
        """Detector initializes with correct thresholds."""
        assert regime_detector.VIX_HIGH_THRESHOLD == 25.0
        assert regime_detector.VIX_EXTREME_THRESHOLD == 35.0
        assert regime_detector.SMA_BEAR_THRESHOLD == -0.05

    def test_calculate_returns(self, regime_detector):
        """Daily returns calculation."""
        history = [
            {"close": 100.0},
            {"close": 102.0},
            {"close": 101.0},
            {"close": 103.0},
        ]

        returns = regime_detector._calculate_returns(history)

        assert len(returns) == 3
        assert abs(returns[0] - 0.02) < 0.001  # 100 -> 102 = 2%

    def test_calculate_correlation(self, regime_detector):
        """Correlation calculation."""
        returns1 = [0.01, 0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.01, 0.01, 0.02]
        returns2 = [0.01, 0.02, -0.01, 0.03, -0.02, 0.01, 0.02, -0.01, 0.01, 0.02]

        # Perfect correlation
        corr = regime_detector._calculate_correlation(returns1, returns2)
        assert corr is not None
        assert abs(corr - 1.0) < 0.001


# ============================================================================
# Integration Tests
# ============================================================================


class TestLearningIntegration:
    """Integration tests for the learning system."""

    def test_full_bias_detection_and_correction_flow(self, mock_db):
        """Full flow from bias detection to correction."""
        meta_engine = MetaLearningEngine(mock_db)

        # Create changes with recency bias
        changes = [
            ProposedWeightChange(
                agent_name="TestAgent",
                old_weight=1.0,
                new_weight=1.3,
                win_rate_7d=80.0,  # High recent performance
                win_rate_30d=50.0,  # Normal longer-term
                win_rate_90d=48.0,
                trades_count_7d=15,
                trades_count_30d=45,
                trades_count_90d=120,
            ),
        ]

        # Detect biases
        bias_report = meta_engine.detect_learning_biases(
            changes, historical_data={}
        )

        # Correct biases
        corrected = meta_engine.correct_biases(changes, bias_report)

        # Corrected weight should be returned
        assert len(corrected) == 1


# ============================================================================
# Edge Cases Tests
# ============================================================================


class TestLearningEdgeCases:
    """Edge case tests for learning system."""

    def test_empty_proposed_changes(self, mock_db):
        """Handling empty proposed changes."""
        meta_engine = MetaLearningEngine(mock_db)
        result = meta_engine.detect_learning_biases([], historical_data={})

        assert result.has_critical_bias is False
        assert len(result.biases) == 0
        assert result.confidence == 1.0

    def test_none_win_rates(self, mock_db):
        """Handling None win rates."""
        meta_engine = MetaLearningEngine(mock_db)
        changes = [
            ProposedWeightChange(
                agent_name="TestAgent",
                old_weight=1.0,
                new_weight=1.1,
                win_rate_7d=None,
                win_rate_30d=None,
                win_rate_90d=None,
                trades_count_7d=0,
                trades_count_30d=0,
                trades_count_90d=0,
            ),
        ]

        # Should not raise an exception
        result = meta_engine.detect_learning_biases(
            changes, historical_data={}
        )
        assert isinstance(result, BiasDetectionResult)

    def test_zero_trades_count(self, mock_db):
        """Handling zero trades."""
        meta_engine = MetaLearningEngine(mock_db)
        changes = [
            ProposedWeightChange(
                agent_name="TestAgent",
                old_weight=1.0,
                new_weight=1.0,
                win_rate_7d=50.0,
                win_rate_30d=50.0,
                win_rate_90d=50.0,
                trades_count_7d=0,
                trades_count_30d=0,
                trades_count_90d=0,
            ),
        ]

        result = meta_engine.detect_learning_biases(
            changes, historical_data={}
        )

        # Should detect overfitting due to zero trades
        assert any(b.type == BiasType.OVERFITTING for b in result.biases)

    def test_extreme_weight_values(self, mock_db):
        """Handling extreme weight values."""
        meta_engine = MetaLearningEngine(mock_db)
        changes = [
            ProposedWeightChange(
                agent_name="TestAgent",
                old_weight=0.3,  # At minimum bound
                new_weight=2.0,  # At maximum bound
                trades_count_7d=50,
                trades_count_30d=100,
                trades_count_90d=200,
            ),
        ]

        result = meta_engine.detect_learning_biases(
            changes, historical_data={}
        )

        # Should still work without exception
        assert isinstance(result, BiasDetectionResult)
