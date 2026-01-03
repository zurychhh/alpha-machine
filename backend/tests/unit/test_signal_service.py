"""
Tests for Signal Service - CRUD operations and risk calculations
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.signal_service import SignalService, get_signal_service
from app.agents.signal_generator import ConsensusSignal, PositionSize
from app.agents.base_agent import AgentSignal, SignalType


class TestSignalService:
    """Tests for SignalService class"""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.flush = Mock()
        db.refresh = Mock()
        db.rollback = Mock()
        db.query = Mock()
        return db

    @pytest.fixture
    def signal_service(self, mock_db):
        """Create a SignalService instance with mock db"""
        return SignalService(mock_db)

    @pytest.fixture
    def sample_consensus(self):
        """Create a sample ConsensusSignal for testing"""
        agent_signals = [
            AgentSignal(
                ticker="NVDA",
                agent_name="TestAgent1",
                signal=SignalType.BUY,
                confidence=0.8,
                raw_score=0.5,
                reasoning="Test reasoning 1",
            ),
            AgentSignal(
                ticker="NVDA",
                agent_name="TestAgent2",
                signal=SignalType.BUY,
                confidence=0.7,
                raw_score=0.4,
                reasoning="Test reasoning 2",
            ),
        ]
        return ConsensusSignal(
            ticker="NVDA",
            signal=SignalType.BUY,
            confidence=0.75,
            raw_score=0.45,
            position_size=PositionSize.NORMAL,
            agent_signals=agent_signals,
            agreement_ratio=1.0,
            reasoning="Strong buy consensus",
        )

    # ===================
    # Risk Parameter Tests
    # ===================

    def test_calculate_stop_loss_buy(self, signal_service):
        """Stop loss for BUY signal is 10% below entry"""
        entry = 100.0
        stop_loss = signal_service._calculate_stop_loss(entry, SignalType.BUY)
        assert stop_loss == 90.0

    def test_calculate_stop_loss_strong_buy(self, signal_service):
        """Stop loss for STRONG_BUY signal is 10% below entry"""
        entry = 100.0
        stop_loss = signal_service._calculate_stop_loss(entry, SignalType.STRONG_BUY)
        assert stop_loss == 90.0

    def test_calculate_stop_loss_sell(self, signal_service):
        """Stop loss for SELL signal is 10% above entry (short position)"""
        entry = 100.0
        stop_loss = signal_service._calculate_stop_loss(entry, SignalType.SELL)
        assert abs(stop_loss - 110.0) < 0.01

    def test_calculate_stop_loss_hold(self, signal_service):
        """Stop loss for HOLD signal equals entry price"""
        entry = 100.0
        stop_loss = signal_service._calculate_stop_loss(entry, SignalType.HOLD)
        assert stop_loss == 100.0

    def test_calculate_target_price_buy(self, signal_service):
        """Target price for BUY signal is 25% above entry"""
        entry = 100.0
        target = signal_service._calculate_target_price(entry, SignalType.BUY)
        assert target == 125.0

    def test_calculate_target_price_sell(self, signal_service):
        """Target price for SELL signal is 25% below entry"""
        entry = 100.0
        target = signal_service._calculate_target_price(entry, SignalType.SELL)
        assert target == 75.0

    def test_calculate_target_price_hold(self, signal_service):
        """Target price for HOLD signal equals entry price"""
        entry = 100.0
        target = signal_service._calculate_target_price(entry, SignalType.HOLD)
        assert target == 100.0

    # ===================
    # Position Sizing Tests
    # ===================

    def test_calculate_shares_normal(self, signal_service):
        """Normal position uses 10% of portfolio"""
        entry = 100.0
        portfolio = 100000.0
        shares = signal_service._calculate_shares(entry, portfolio, PositionSize.NORMAL)
        # 10% of 100000 = 10000 / 100 = 100 shares
        assert shares == 100

    def test_calculate_shares_small(self, signal_service):
        """Small position uses 2.5% of portfolio"""
        entry = 100.0
        portfolio = 100000.0
        shares = signal_service._calculate_shares(entry, portfolio, PositionSize.SMALL)
        # 10% * 0.25 of 100000 = 2500 / 100 = 25 shares
        assert shares == 25

    def test_calculate_shares_large(self, signal_service):
        """Large position uses 15% of portfolio"""
        entry = 100.0
        portfolio = 100000.0
        shares = signal_service._calculate_shares(entry, portfolio, PositionSize.LARGE)
        # 10% * 1.5 of 100000 = 15000 / 100 = 150 shares
        assert shares == 150

    def test_calculate_shares_none(self, signal_service):
        """No position for NONE size"""
        entry = 100.0
        portfolio = 100000.0
        shares = signal_service._calculate_shares(entry, portfolio, PositionSize.NONE)
        assert shares == 0

    def test_calculate_shares_zero_price(self, signal_service):
        """No shares when price is zero"""
        shares = signal_service._calculate_shares(0, 100000.0, PositionSize.NORMAL)
        assert shares == 0

    def test_calculate_shares_expensive_stock(self, signal_service):
        """Correct shares for expensive stocks"""
        entry = 1000.0
        portfolio = 100000.0
        shares = signal_service._calculate_shares(entry, portfolio, PositionSize.NORMAL)
        # 10% of 100000 = 10000 / 1000 = 10 shares
        assert shares == 10

    # ===================
    # Confidence Mapping Tests
    # ===================

    def test_map_confidence_high(self, signal_service):
        """High confidence (0.8+) maps to 5"""
        assert signal_service._map_confidence(0.9) == 5
        assert signal_service._map_confidence(0.8) == 5

    def test_map_confidence_medium_high(self, signal_service):
        """Medium-high confidence (0.6-0.8) maps to 4"""
        assert signal_service._map_confidence(0.7) == 4
        assert signal_service._map_confidence(0.6) == 4

    def test_map_confidence_medium(self, signal_service):
        """Medium confidence (0.4-0.6) maps to 3"""
        assert signal_service._map_confidence(0.5) == 3
        assert signal_service._map_confidence(0.4) == 3

    def test_map_confidence_low(self, signal_service):
        """Low confidence (0.2-0.4) maps to 2"""
        assert signal_service._map_confidence(0.3) == 2
        assert signal_service._map_confidence(0.2) == 2

    def test_map_confidence_very_low(self, signal_service):
        """Very low confidence (<0.2) maps to 1"""
        assert signal_service._map_confidence(0.1) == 1
        assert signal_service._map_confidence(0.0) == 1

    # ===================
    # Signal Type Mapping Tests
    # ===================

    def test_map_signal_type_strong_buy(self, signal_service):
        """STRONG_BUY maps to BUY"""
        assert signal_service._map_signal_type(SignalType.STRONG_BUY) == "BUY"

    def test_map_signal_type_buy(self, signal_service):
        """BUY maps to BUY"""
        assert signal_service._map_signal_type(SignalType.BUY) == "BUY"

    def test_map_signal_type_hold(self, signal_service):
        """HOLD maps to HOLD"""
        assert signal_service._map_signal_type(SignalType.HOLD) == "HOLD"

    def test_map_signal_type_sell(self, signal_service):
        """SELL maps to SELL"""
        assert signal_service._map_signal_type(SignalType.SELL) == "SELL"

    def test_map_signal_type_strong_sell(self, signal_service):
        """STRONG_SELL maps to SELL"""
        assert signal_service._map_signal_type(SignalType.STRONG_SELL) == "SELL"

    # ===================
    # Save Signal Tests
    # ===================

    def test_save_signal_creates_record(self, signal_service, mock_db, sample_consensus):
        """save_signal creates a Signal record"""
        # Mock the Signal class
        with patch("app.services.signal_service.Signal") as MockSignal:
            mock_signal = Mock()
            mock_signal.id = 1
            mock_signal.entry_price = Decimal("100.00")
            mock_signal.stop_loss = Decimal("90.00")
            mock_signal.target_price = Decimal("125.00")
            mock_signal.position_size = 100
            MockSignal.return_value = mock_signal

            with patch("app.services.signal_service.AgentAnalysis"):
                result = signal_service.save_signal(
                    consensus=sample_consensus,
                    entry_price=100.0,
                    portfolio_value=100000.0,
                )

                # Verify Signal was created
                MockSignal.assert_called_once()
                mock_db.add.assert_called()
                mock_db.commit.assert_called_once()

    def test_save_signal_calculates_risk_params(self, signal_service, mock_db, sample_consensus):
        """save_signal calculates correct risk parameters"""
        with patch("app.services.signal_service.Signal") as MockSignal:
            mock_signal = Mock()
            mock_signal.id = 1
            MockSignal.return_value = mock_signal

            with patch("app.services.signal_service.AgentAnalysis"):
                signal_service.save_signal(
                    consensus=sample_consensus,
                    entry_price=100.0,
                    portfolio_value=100000.0,
                )

                # Check Signal was created with correct parameters
                call_kwargs = MockSignal.call_args[1]
                assert call_kwargs["ticker"] == "NVDA"
                assert call_kwargs["signal_type"] == "BUY"
                assert float(call_kwargs["stop_loss"]) == 90.0
                assert float(call_kwargs["target_price"]) == 125.0

    # ===================
    # Get Signals Tests
    # ===================

    def test_get_signal_by_id(self, signal_service, mock_db):
        """get_signal returns signal by ID"""
        mock_signal = Mock()
        mock_signal.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_signal

        result = signal_service.get_signal(1)
        assert result == mock_signal

    def test_get_signal_not_found(self, signal_service, mock_db):
        """get_signal returns None when not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = signal_service.get_signal(999)
        assert result is None

    def test_get_signals_with_filters(self, signal_service, mock_db):
        """get_signals applies filters correctly"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        signal_service.get_signals(ticker="NVDA", signal_type="BUY", status="PENDING")

        # Verify filters were applied
        assert mock_query.filter.call_count >= 3

    # ===================
    # Update Status Tests
    # ===================

    def test_update_signal_status_approved(self, signal_service, mock_db):
        """update_signal_status updates to APPROVED"""
        mock_signal = Mock()
        mock_signal.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_signal

        result = signal_service.update_signal_status(1, "APPROVED")

        assert mock_signal.status == "APPROVED"
        mock_db.commit.assert_called_once()

    def test_update_signal_status_executed(self, signal_service, mock_db):
        """update_signal_status sets executed_at timestamp"""
        mock_signal = Mock()
        mock_signal.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_signal

        result = signal_service.update_signal_status(1, "EXECUTED")

        assert mock_signal.status == "EXECUTED"
        assert mock_signal.executed_at is not None

    def test_update_signal_status_closed_with_pnl(self, signal_service, mock_db):
        """update_signal_status sets pnl when closing"""
        mock_signal = Mock()
        mock_signal.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_signal

        result = signal_service.update_signal_status(1, "CLOSED", pnl=1500.50)

        assert mock_signal.status == "CLOSED"
        assert mock_signal.closed_at is not None
        assert mock_signal.pnl == Decimal("1500.50")

    def test_update_signal_status_not_found(self, signal_service, mock_db):
        """update_signal_status returns None when signal not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = signal_service.update_signal_status(999, "APPROVED")
        assert result is None

    # ===================
    # Statistics Tests
    # ===================

    def test_get_statistics_empty(self, signal_service, mock_db):
        """get_statistics returns zeros when no signals"""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        stats = signal_service.get_statistics(days=30)

        assert stats["total_signals"] == 0
        assert stats["win_rate"] is None

    def test_get_statistics_with_signals(self, signal_service, mock_db):
        """get_statistics calculates correct values"""
        # Create mock signals
        mock_signals = [
            Mock(signal_type="BUY", status="PENDING", pnl=None),
            Mock(signal_type="BUY", status="CLOSED", pnl=Decimal("100")),
            Mock(signal_type="SELL", status="CLOSED", pnl=Decimal("-50")),
            Mock(signal_type="HOLD", status="PENDING", pnl=None),
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_signals

        stats = signal_service.get_statistics(days=30)

        assert stats["total_signals"] == 4
        assert stats["by_type"]["BUY"] == 2
        assert stats["by_type"]["HOLD"] == 1
        assert stats["closed_signals"] == 2
        # 1 winner (100) / 2 closed = 50% win rate
        assert stats["win_rate"] == 0.5
        # (100 + -50) / 2 = 25 avg pnl
        assert stats["average_pnl"] == 25.0

    # ===================
    # Signal to Dict Tests
    # ===================

    def test_signal_to_dict(self, signal_service):
        """signal_to_dict converts signal to dictionary"""
        mock_signal = Mock()
        mock_signal.id = 1
        mock_signal.ticker = "NVDA"
        mock_signal.signal_type = "BUY"
        mock_signal.confidence = 4
        mock_signal.entry_price = Decimal("100.00")
        mock_signal.target_price = Decimal("125.00")
        mock_signal.stop_loss = Decimal("90.00")
        mock_signal.position_size = 100
        mock_signal.status = "PENDING"
        mock_signal.timestamp = datetime(2024, 1, 1, 10, 0, 0)
        mock_signal.executed_at = None
        mock_signal.closed_at = None
        mock_signal.pnl = None
        mock_signal.notes = "Test signal"
        mock_signal.agent_analyses = []

        result = signal_service.signal_to_dict(mock_signal)

        assert result["id"] == 1
        assert result["ticker"] == "NVDA"
        assert result["signal_type"] == "BUY"
        assert result["entry_price"] == 100.0
        assert result["target_price"] == 125.0
        assert result["stop_loss"] == 90.0


class TestGetSignalService:
    """Tests for get_signal_service factory function"""

    def test_returns_signal_service(self):
        """get_signal_service returns SignalService instance"""
        mock_db = Mock()
        service = get_signal_service(mock_db)
        assert isinstance(service, SignalService)
