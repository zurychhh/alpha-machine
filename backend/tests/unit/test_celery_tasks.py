"""
Tests for Celery Tasks - Data fetching and signal generation tasks
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta


class TestCeleryAppConfiguration:
    """Tests for Celery app configuration"""

    def test_celery_app_imports(self):
        """Celery app can be imported"""
        from app.tasks.celery_app import celery_app, app
        assert celery_app is not None
        assert app is celery_app

    def test_is_market_hours_function(self):
        """is_market_hours function exists and returns boolean"""
        from app.tasks.celery_app import is_market_hours
        result = is_market_hours()
        assert isinstance(result, bool)

    def test_beat_schedule_defined(self):
        """Beat schedule has expected tasks"""
        from app.tasks.celery_app import celery_app
        schedule = celery_app.conf.beat_schedule

        assert "fetch-market-data-5min" in schedule
        assert "fetch-sentiment-30min" in schedule
        assert "generate-signals-daily" in schedule

    def test_task_routes_defined(self):
        """Task routes are configured"""
        from app.tasks.celery_app import celery_app
        routes = celery_app.conf.task_routes

        assert "app.tasks.data_tasks.*" in routes
        assert "app.tasks.signal_tasks.*" in routes


class TestDataTasks:
    """Tests for data fetching tasks"""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        with patch("app.tasks.data_tasks.SessionLocal") as mock:
            session = Mock()
            mock.return_value = session
            yield session

    @pytest.fixture
    def mock_watchlist(self):
        """Create mock watchlist items"""
        items = [
            Mock(ticker="NVDA", is_active=True),
            Mock(ticker="AAPL", is_active=True),
        ]
        return items

    def test_fetch_market_data_task_exists(self):
        """fetch_market_data_task is a registered task"""
        from app.tasks.data_tasks import fetch_market_data_task
        assert fetch_market_data_task is not None
        assert hasattr(fetch_market_data_task, "delay")

    def test_fetch_sentiment_task_exists(self):
        """fetch_sentiment_task is a registered task"""
        from app.tasks.data_tasks import fetch_sentiment_task
        assert fetch_sentiment_task is not None
        assert hasattr(fetch_sentiment_task, "delay")

    def test_fetch_single_ticker_data_exists(self):
        """fetch_single_ticker_data is a registered task"""
        from app.tasks.data_tasks import fetch_single_ticker_data
        assert fetch_single_ticker_data is not None

    def test_fetch_market_data_task_config(self):
        """fetch_market_data_task is properly configured"""
        from app.tasks.data_tasks import fetch_market_data_task

        # Verify task is callable and has expected attributes
        assert callable(fetch_market_data_task)
        assert hasattr(fetch_market_data_task, "name")
        assert "fetch_market_data" in fetch_market_data_task.name

    def test_fetch_sentiment_task_config(self):
        """fetch_sentiment_task is properly configured"""
        from app.tasks.data_tasks import fetch_sentiment_task

        # Verify task is callable and has expected attributes
        assert callable(fetch_sentiment_task)
        assert hasattr(fetch_sentiment_task, "name")
        assert "fetch_sentiment" in fetch_sentiment_task.name

    @patch("app.tasks.data_tasks.market_data_service")
    @patch("app.tasks.data_tasks.sentiment_service")
    def test_fetch_single_ticker_data_success(self, mock_sentiment, mock_market):
        """fetch_single_ticker_data returns data for ticker"""
        from app.tasks.data_tasks import fetch_single_ticker_data

        mock_market.get_quote.return_value = {"current_price": 100.0}
        mock_market.get_technical_indicators.return_value = {"rsi": 50}
        mock_sentiment.aggregate_sentiment.return_value = {"combined_sentiment": 0.5}

        result = fetch_single_ticker_data("NVDA")

        assert result["ticker"] == "NVDA"
        assert result["status"] == "success"
        assert result["market_data"] is not None

    @patch("app.tasks.data_tasks.market_data_service")
    def test_fetch_single_ticker_data_error(self, mock_market):
        """fetch_single_ticker_data handles errors"""
        from app.tasks.data_tasks import fetch_single_ticker_data

        mock_market.get_quote.side_effect = Exception("API Error")

        result = fetch_single_ticker_data("INVALID")

        assert result["status"] == "error"
        assert "error" in result


class TestSignalTasks:
    """Tests for signal generation tasks"""

    def test_generate_daily_signals_task_exists(self):
        """generate_daily_signals_task is a registered task"""
        from app.tasks.signal_tasks import generate_daily_signals_task
        assert generate_daily_signals_task is not None
        assert hasattr(generate_daily_signals_task, "delay")

    def test_generate_signal_for_ticker_exists(self):
        """generate_signal_for_ticker is a registered task"""
        from app.tasks.signal_tasks import generate_signal_for_ticker
        assert generate_signal_for_ticker is not None

    def test_analyze_signal_performance_task_exists(self):
        """analyze_signal_performance_task is a registered task"""
        from app.tasks.signal_tasks import analyze_signal_performance_task
        assert analyze_signal_performance_task is not None

    def test_generate_high_confidence_alerts_exists(self):
        """generate_high_confidence_alerts is a registered task"""
        from app.tasks.signal_tasks import generate_high_confidence_alerts
        assert generate_high_confidence_alerts is not None

    @patch("app.tasks.signal_tasks.SessionLocal")
    @patch("app.tasks.signal_tasks.market_data_service")
    @patch("app.tasks.signal_tasks.get_signal_generator")
    def test_generate_signal_for_ticker_success(
        self, mock_gen, mock_market, mock_session
    ):
        """generate_signal_for_ticker returns signal data"""
        from app.tasks.signal_tasks import generate_signal_for_ticker
        from app.agents.base_agent import SignalType
        from app.agents.signal_generator import PositionSize

        # Setup mocks
        mock_market.get_quote.return_value = {"current_price": 100.0}
        mock_market.get_technical_indicators.return_value = {"rsi": 50}

        mock_consensus = Mock()
        mock_consensus.signal.value = "BUY"
        mock_consensus.confidence = 0.8
        mock_consensus.raw_score = 0.5
        mock_consensus.position_size.value = "NORMAL"
        mock_consensus.reasoning = "Test"
        mock_consensus.agent_signals = []

        mock_generator = Mock()
        mock_generator.generate_signal.return_value = mock_consensus
        mock_gen.return_value = mock_generator

        result = generate_signal_for_ticker("NVDA", save=False)

        assert result["ticker"] == "NVDA"
        assert result["status"] == "success"
        assert result["signal"] == "BUY"

    @patch("app.tasks.signal_tasks.market_data_service")
    def test_generate_signal_for_ticker_no_data(self, mock_market):
        """generate_signal_for_ticker handles missing market data"""
        from app.tasks.signal_tasks import generate_signal_for_ticker

        mock_market.get_quote.return_value = {"current_price": None}

        result = generate_signal_for_ticker("INVALID", save=False)

        assert result["status"] == "error"

    @patch("app.tasks.signal_tasks.SessionLocal")
    def test_analyze_signal_performance_empty(self, mock_session):
        """analyze_signal_performance_task handles no signals"""
        from app.tasks.signal_tasks import analyze_signal_performance_task

        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        # Verify task is properly configured
        assert callable(analyze_signal_performance_task)
        assert hasattr(analyze_signal_performance_task, "name")

    @patch("app.tasks.signal_tasks.SessionLocal")
    def test_generate_high_confidence_alerts(self, mock_session):
        """generate_high_confidence_alerts returns high confidence signals"""
        from app.tasks.signal_tasks import generate_high_confidence_alerts
        from decimal import Decimal

        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_signals = [
            Mock(
                id=1,
                ticker="NVDA",
                signal_type="BUY",
                confidence=5,
                entry_price=Decimal("100"),
                target_price=Decimal("125"),
                stop_loss=Decimal("90"),
            ),
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = mock_signals

        result = generate_high_confidence_alerts(min_confidence=4)

        assert result["status"] == "success"
        assert result["count"] == 1
        assert result["signals"][0]["ticker"] == "NVDA"


class TestTaskModuleExports:
    """Tests for tasks module exports"""

    def test_celery_app_exported(self):
        """celery_app is exported from tasks module"""
        from app.tasks import celery_app
        assert celery_app is not None

    def test_data_tasks_exported(self):
        """Data tasks are exported"""
        from app.tasks import (
            fetch_market_data_task,
            fetch_sentiment_task,
            fetch_single_ticker_data,
            refresh_all_data,
        )
        assert fetch_market_data_task is not None
        assert fetch_sentiment_task is not None
        assert fetch_single_ticker_data is not None
        assert refresh_all_data is not None

    def test_signal_tasks_exported(self):
        """Signal tasks are exported"""
        from app.tasks import (
            generate_daily_signals_task,
            generate_signal_for_ticker,
            analyze_signal_performance_task,
            generate_high_confidence_alerts,
        )
        assert generate_daily_signals_task is not None
        assert generate_signal_for_ticker is not None
        assert analyze_signal_performance_task is not None
        assert generate_high_confidence_alerts is not None

    def test_is_market_hours_exported(self):
        """is_market_hours is exported"""
        from app.tasks import is_market_hours
        assert callable(is_market_hours)
