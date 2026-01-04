"""
Unit tests for backtesting module.

Tests signal ranking, portfolio allocation, and backtest engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
from decimal import Decimal

from app.services.signal_ranker import SignalRanker, signal_ranker
from app.services.portfolio_allocator import PortfolioAllocator, portfolio_allocator
from app.services.backtesting import BacktestEngine, backtest_engine
from app.models.signal import Signal
from app.models.backtest_result import BacktestResult


# ============================================================================
# Signal Ranker Tests
# ============================================================================


class TestSignalRanker:
    """Tests for SignalRanker service."""

    def create_mock_signal(
        self,
        ticker: str = "NVDA",
        signal_type: str = "BUY",
        confidence: int = 4,
        entry_price: float = 100.0,
        target_price: float = 125.0,
        stop_loss: float = 90.0,
    ) -> Mock:
        """Create a mock Signal object for testing."""
        signal = Mock(spec=Signal)
        signal.id = 1
        signal.ticker = ticker
        signal.signal_type = signal_type
        signal.confidence = confidence
        signal.entry_price = Decimal(str(entry_price))
        signal.target_price = Decimal(str(target_price))
        signal.stop_loss = Decimal(str(stop_loss))
        signal.timestamp = datetime.now()
        return signal

    def test_rank_signals_empty_list(self):
        """Ranker handles empty signal list."""
        ranker = SignalRanker()
        result = ranker.rank_signals([], Mock())
        assert result == []

    def test_rank_signals_filters_non_buy(self):
        """Ranker only includes BUY signals."""
        ranker = SignalRanker()
        buy_signal = self.create_mock_signal(signal_type="BUY")
        sell_signal = self.create_mock_signal(signal_type="SELL")
        hold_signal = self.create_mock_signal(signal_type="HOLD")

        result = ranker.rank_signals([buy_signal, sell_signal, hold_signal], Mock())

        assert len(result) == 1
        assert result[0]["signal"].signal_type == "BUY"

    def test_rank_signals_calculates_score(self):
        """Ranker calculates composite score correctly."""
        ranker = SignalRanker()
        signal = self.create_mock_signal(
            confidence=5,
            entry_price=100.0,
            target_price=125.0,  # 25% expected return
            stop_loss=90.0,  # 10% downside
        )

        result = ranker.rank_signals([signal], Mock())

        assert len(result) == 1
        assert result[0]["score"] > 0
        assert result[0]["expected_return"] == 0.25
        assert result[0]["risk_factor"] == 1.0  # 10% * 10 = 1.0
        assert result[0]["confidence"] == 5
        assert result[0]["rank"] == 1

    def test_rank_signals_sorts_by_score(self):
        """Ranker sorts signals by score descending."""
        ranker = SignalRanker()
        high_conf_signal = self.create_mock_signal(confidence=5, target_price=150.0)
        low_conf_signal = self.create_mock_signal(confidence=2, target_price=110.0)

        result = ranker.rank_signals([low_conf_signal, high_conf_signal], Mock())

        assert len(result) == 2
        assert result[0]["rank"] == 1
        assert result[0]["confidence"] == 5  # Higher score first
        assert result[1]["rank"] == 2
        assert result[1]["confidence"] == 2

    def test_rank_signals_handles_missing_prices(self):
        """Ranker uses defaults when prices are missing."""
        ranker = SignalRanker()
        signal = self.create_mock_signal()
        signal.entry_price = None
        signal.target_price = None
        signal.stop_loss = None

        result = ranker.rank_signals([signal], Mock())

        assert len(result) == 1
        assert result[0]["expected_return"] == 0.10  # Default 10%
        assert result[0]["risk_factor"] == 1.5  # Default medium risk

    def test_get_top_signals(self):
        """get_top_signals returns limited results."""
        ranker = SignalRanker()
        signals = [
            self.create_mock_signal(confidence=i) for i in range(5, 0, -1)
        ]

        result = ranker.get_top_signals(signals, Mock(), top_n=3)

        assert len(result) == 3
        assert result[0]["rank"] == 1


# ============================================================================
# Portfolio Allocator Tests
# ============================================================================


class TestPortfolioAllocator:
    """Tests for PortfolioAllocator service."""

    def create_ranked_signal(
        self,
        ticker: str = "NVDA",
        entry_price: float = 100.0,
        score: float = 0.5,
    ) -> dict:
        """Create a ranked signal dict for testing."""
        signal = Mock(spec=Signal)
        signal.id = 1
        signal.ticker = ticker
        signal.entry_price = Decimal(str(entry_price))
        return {
            "signal": signal,
            "score": score,
            "expected_return": 0.25,
            "risk_factor": 1.0,
            "confidence": 4,
        }

    def test_allocate_empty_signals(self):
        """Allocator handles empty signal list."""
        allocator = PortfolioAllocator()

        for mode in ["CORE_FOCUS", "BALANCED", "DIVERSIFIED"]:
            result = allocator.allocate([], 50000.0, mode)
            assert result == []

    def test_allocate_core_focus(self):
        """CORE_FOCUS allocates 60% to top signal."""
        allocator = PortfolioAllocator()
        signals = [self.create_ranked_signal(entry_price=100.0) for _ in range(5)]

        result = allocator.allocate(signals, 50000.0, "CORE_FOCUS")

        # Should have 4 positions (1 core + 3 satellites)
        assert len(result) == 4

        # Core position
        assert result[0]["position_type"] == "CORE"
        assert result[0]["allocation_pct"] == 0.60
        assert result[0]["allocation_dollars"] == 30000.0
        assert result[0]["shares"] == 300  # 30000 / 100

        # Satellites (10% each)
        for i in range(1, 4):
            assert result[i]["position_type"] == "SATELLITE"
            assert result[i]["allocation_pct"] == 0.10
            assert result[i]["allocation_dollars"] == 5000.0
            assert result[i]["shares"] == 50

    def test_allocate_balanced(self):
        """BALANCED allocates 40% to top signal."""
        allocator = PortfolioAllocator()
        signals = [self.create_ranked_signal(entry_price=100.0) for _ in range(5)]

        result = allocator.allocate(signals, 50000.0, "BALANCED")

        # Should have 5 positions (1 core + 4 satellites)
        assert len(result) == 5

        # Core position
        assert result[0]["position_type"] == "CORE"
        assert result[0]["allocation_pct"] == 0.40
        assert result[0]["allocation_dollars"] == 20000.0

        # Satellites (12.5% each)
        for i in range(1, 5):
            assert result[i]["position_type"] == "SATELLITE"
            assert result[i]["allocation_pct"] == 0.125
            assert result[i]["allocation_dollars"] == 6250.0

    def test_allocate_diversified(self):
        """DIVERSIFIED allocates equally across top 5."""
        allocator = PortfolioAllocator()
        signals = [self.create_ranked_signal(entry_price=100.0) for _ in range(5)]

        result = allocator.allocate(signals, 50000.0, "DIVERSIFIED")

        # Should have 5 equal positions
        assert len(result) == 5

        for pos in result:
            assert pos["position_type"] == "EQUAL"
            assert abs(pos["allocation_pct"] - 0.16) < 0.01  # ~16% each
            assert abs(pos["allocation_dollars"] - 8000.0) < 1.0

    def test_allocate_invalid_mode_raises(self):
        """Allocator raises on invalid mode."""
        allocator = PortfolioAllocator()
        signals = [self.create_ranked_signal()]

        with pytest.raises(ValueError, match="Unknown allocation mode"):
            allocator.allocate(signals, 50000.0, "INVALID_MODE")

    def test_allocate_fewer_signals_than_slots(self):
        """Allocator handles fewer signals than allocation slots."""
        allocator = PortfolioAllocator()
        signals = [self.create_ranked_signal()]  # Only 1 signal

        result = allocator.allocate(signals, 50000.0, "CORE_FOCUS")

        # Should only have 1 position (the core)
        assert len(result) == 1
        assert result[0]["position_type"] == "CORE"

    def test_get_cash_reserve(self):
        """get_cash_reserve returns correct amounts."""
        allocator = PortfolioAllocator()
        capital = 50000.0

        assert allocator.get_cash_reserve("CORE_FOCUS", capital) == 5000.0
        assert allocator.get_cash_reserve("BALANCED", capital) == 5000.0
        assert allocator.get_cash_reserve("DIVERSIFIED", capital) == 10000.0

    def test_get_mode_description(self):
        """get_mode_description returns valid info."""
        allocator = PortfolioAllocator()

        for mode in ["CORE_FOCUS", "BALANCED", "DIVERSIFIED"]:
            desc = allocator.get_mode_description(mode)
            assert "name" in desc
            assert "description" in desc
            assert "risk_level" in desc


# ============================================================================
# Backtest Engine Tests
# ============================================================================


class TestBacktestEngine:
    """Tests for BacktestEngine service."""

    def create_mock_signal(
        self,
        ticker: str = "NVDA",
        signal_type: str = "BUY",
        confidence: int = 4,
        entry_price: float = 100.0,
        target_price: float = 125.0,
        stop_loss: float = 90.0,
    ) -> Mock:
        """Create a mock Signal object."""
        signal = Mock(spec=Signal)
        signal.id = 1
        signal.ticker = ticker
        signal.signal_type = signal_type
        signal.confidence = confidence
        signal.entry_price = Decimal(str(entry_price))
        signal.target_price = Decimal(str(target_price))
        signal.stop_loss = Decimal(str(stop_loss))
        signal.timestamp = datetime(2024, 12, 15)
        return signal

    def test_group_signals_by_day(self):
        """Engine groups signals by date correctly."""
        engine = BacktestEngine()

        signal1 = self.create_mock_signal()
        signal1.timestamp = datetime(2024, 12, 15, 10, 30)

        signal2 = self.create_mock_signal()
        signal2.timestamp = datetime(2024, 12, 15, 14, 45)

        signal3 = self.create_mock_signal()
        signal3.timestamp = datetime(2024, 12, 16, 9, 0)

        result = engine._group_signals_by_day([signal1, signal2, signal3])

        assert len(result) == 2
        assert len(result["2024-12-15"]) == 2
        assert len(result["2024-12-16"]) == 1

    @patch("app.services.backtesting.market_data_service")
    def test_simulate_hold_period_stop_loss(self, mock_market):
        """Simulate exit at stop-loss."""
        engine = BacktestEngine()
        signal = self.create_mock_signal(
            entry_price=100.0,
            stop_loss=90.0,
            target_price=125.0,
        )

        # Simulate price hitting stop loss on day 2
        mock_market.get_historical_data.return_value = [
            {"date": "2024-12-16", "low": 95.0, "high": 102.0, "close": 97.0},
            {"date": "2024-12-17", "low": 88.0, "high": 96.0, "close": 89.0},  # Hits stop
        ]

        exit_price, exit_date, exit_reason = engine._simulate_hold_period(
            signal=signal,
            entry_date=date(2024, 12, 15),
            entry_price=100.0,
            hold_period_days=7,
        )

        assert exit_reason == "STOP_LOSS"
        assert exit_price == 90.0

    @patch("app.services.backtesting.market_data_service")
    def test_simulate_hold_period_take_profit(self, mock_market):
        """Simulate exit at take-profit."""
        engine = BacktestEngine()
        signal = self.create_mock_signal(
            entry_price=100.0,
            stop_loss=90.0,
            target_price=125.0,
        )

        # Simulate price hitting target on day 3
        mock_market.get_historical_data.return_value = [
            {"date": "2024-12-16", "low": 100.0, "high": 105.0, "close": 104.0},
            {"date": "2024-12-17", "low": 103.0, "high": 115.0, "close": 112.0},
            {"date": "2024-12-18", "low": 110.0, "high": 130.0, "close": 128.0},  # Hits target
        ]

        exit_price, exit_date, exit_reason = engine._simulate_hold_period(
            signal=signal,
            entry_date=date(2024, 12, 15),
            entry_price=100.0,
            hold_period_days=7,
        )

        assert exit_reason == "TAKE_PROFIT"
        assert exit_price == 125.0

    def test_calculate_metrics_empty_trades(self):
        """Metrics calculation handles empty trades."""
        engine = BacktestEngine()

        result = engine._calculate_metrics([], 50000.0, "test-id")

        assert result["capital"]["starting"] == 50000.0
        assert result["capital"]["ending"] == 50000.0
        assert result["capital"]["return_pct"] == 0.0
        assert result["trades"]["total"] == 0
        assert result["trades"]["win_rate"] == 0.0

    def test_calculate_metrics_with_trades(self):
        """Metrics calculation with trades."""
        engine = BacktestEngine()

        # Create mock trades
        trades = []
        for i, (pnl, result) in enumerate([
            (500.0, "WIN"),
            (300.0, "WIN"),
            (-200.0, "LOSS"),
            (400.0, "WIN"),
        ]):
            trade = Mock(spec=BacktestResult)
            trade.id = i + 1
            trade.pnl = Decimal(str(pnl))
            trade.pnl_pct = Decimal(str(pnl / 1000))  # Simplified
            trade.trade_result = result
            trade.days_held = 5
            trades.append(trade)

        result = engine._calculate_metrics(trades, 50000.0, "test-id")

        assert result["trades"]["total"] == 4
        assert result["trades"]["wins"] == 3
        assert result["trades"]["losses"] == 1
        assert result["trades"]["win_rate"] == 0.75
        assert result["metrics"]["total_pnl"] == 1000.0  # 500+300-200+400
        assert result["capital"]["ending"] == 51000.0

    @patch("app.services.backtesting.market_data_service")
    @patch("app.services.backtesting.signal_ranker")
    @patch("app.services.backtesting.portfolio_allocator")
    def test_run_backtest_no_signals(self, mock_allocator, mock_ranker, mock_market):
        """Backtest returns error when no signals found."""
        engine = BacktestEngine()
        mock_db = MagicMock()

        # Mock the SQLAlchemy query chain to return empty list
        # query().filter().order_by().all() returns []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = engine.run_backtest(
            db=mock_db,
            start_date="2024-12-01",
            end_date="2024-12-31",
            mode="CORE_FOCUS",
        )

        assert "error" in result
        assert "No BUY signals found" in result["error"]


# ============================================================================
# BacktestResult Model Tests
# ============================================================================


class TestBacktestResultModel:
    """Tests for BacktestResult SQLAlchemy model."""

    def test_model_repr(self):
        """Model __repr__ returns expected format."""
        result = BacktestResult(
            backtest_id="test-backtest-1234-5678",
            signal_id=1,
            trade_result="WIN",
            pnl=Decimal("500.00"),
        )

        repr_str = repr(result)

        assert "test-bac" in repr_str
        assert "WIN" in repr_str
        assert "500.00" in repr_str

    def test_model_fields(self):
        """Model has all required fields."""
        result = BacktestResult(
            backtest_id="uuid-123",
            signal_id=1,
            entry_date=date(2024, 12, 15),
            exit_date=date(2024, 12, 22),
            entry_price=Decimal("100.00"),
            exit_price=Decimal("110.00"),
            shares=50,
            pnl=Decimal("500.00"),
            pnl_pct=Decimal("10.000"),
            trade_result="WIN",
            days_held=7,
            exit_reason="TAKE_PROFIT",
            position_type="CORE",
            allocation_pct=Decimal("0.600"),
        )

        assert result.backtest_id == "uuid-123"
        assert result.shares == 50
        assert result.trade_result == "WIN"
        assert result.position_type == "CORE"


# ============================================================================
# Integration Tests (Light)
# ============================================================================


class TestBacktestIntegration:
    """Light integration tests for backtest components working together."""

    def test_ranker_to_allocator_flow(self):
        """Signal ranker output works with allocator input."""
        ranker = SignalRanker()
        allocator = PortfolioAllocator()

        # Create mock signals
        signals = []
        for i in range(5):
            signal = Mock(spec=Signal)
            signal.id = i + 1
            signal.ticker = f"STOCK{i}"
            signal.signal_type = "BUY"
            signal.confidence = 5 - i  # 5, 4, 3, 2, 1
            signal.entry_price = Decimal("100.0")
            signal.target_price = Decimal("125.0")
            signal.stop_loss = Decimal("90.0")
            signals.append(signal)

        # Rank signals
        ranked = ranker.rank_signals(signals, Mock())

        # Should be sorted by confidence (highest first)
        assert ranked[0]["confidence"] == 5
        assert ranked[4]["confidence"] == 1

        # Allocate using ranked signals
        positions = allocator.allocate(ranked, 50000.0, "CORE_FOCUS")

        # Core position should be the highest ranked
        assert positions[0]["position_type"] == "CORE"
        assert positions[0]["signal"].confidence == 5
