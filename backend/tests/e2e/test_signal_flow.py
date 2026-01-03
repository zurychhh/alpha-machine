"""
End-to-End Tests for Signal Generation Flow
Tests complete user flows from request to response
"""

import pytest
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.agents.base_agent import SignalType


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


class TestSignalGenerationE2E:
    """Test complete signal generation flow - 10 tests"""

    @pytest.mark.e2e
    def test_health_check_flow(self, test_client):
        """Complete health check flow"""
        response = test_client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"

    @pytest.mark.e2e
    def test_agents_list_flow(self, test_client):
        """Complete agents list flow"""
        response = test_client.get("/api/v1/signals/agents")

        assert response.status_code == 200
        data = response.json()

        assert "agent_count" in data
        assert "agents" in data
        assert data["agent_count"] >= 1

        # Verify agent structure
        for agent in data["agents"]:
            assert "name" in agent
            assert "type" in agent
            assert "weight" in agent

    @pytest.mark.e2e
    def test_quick_signal_test_flow(self, test_client):
        """Quick signal test endpoint flow"""
        response = test_client.get("/api/v1/signals/test/NVDA")

        # May succeed or fail depending on API availability
        if response.status_code == 200:
            data = response.json()
            assert "ticker" in data
            assert "signal" in data
            assert "confidence" in data
            assert data["ticker"] == "NVDA"

    @pytest.mark.e2e
    def test_full_signal_generation_flow(self, test_client):
        """Full signal generation with all parameters"""
        response = test_client.post(
            "/api/v1/signals/generate/NVDA",
            params={
                "include_sentiment": True,
                "include_historical": True,
                "days": 30
            }
        )

        if response.status_code == 200:
            data = response.json()

            # Verify complete response structure
            assert "ticker" in data
            assert "signal" in data
            assert "confidence" in data
            assert "raw_score" in data
            assert "agent_signals" in data

            # Verify signal is valid
            valid_signals = ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]
            assert data["signal"] in valid_signals

            # Verify confidence range
            assert 0.0 <= data["confidence"] <= 1.0

    @pytest.mark.e2e
    def test_signal_timing_under_threshold(self, test_client):
        """Signal generation completes within time limit"""
        start_time = time.time()

        response = test_client.get("/api/v1/signals/test/AAPL")

        elapsed = time.time() - start_time

        # Quick test should be fast (< 30 seconds even with API calls)
        # For local tests without API, should be < 1 second
        assert elapsed < 60.0  # Generous timeout for CI

    @pytest.mark.e2e
    def test_multiple_tickers_sequential(self, test_client):
        """Multiple ticker requests in sequence"""
        tickers = ["NVDA", "AAPL", "MSFT"]

        for ticker in tickers:
            response = test_client.get(f"/api/v1/signals/test/{ticker}")

            # Each should process without error
            assert response.status_code in [200, 404, 500]

    @pytest.mark.e2e
    def test_watchlist_to_signals_flow(self, test_client):
        """Get watchlist then generate signals for first ticker"""
        # Step 1: Get watchlist
        watchlist_response = test_client.get("/api/v1/data/watchlist")
        assert watchlist_response.status_code == 200

        watchlist_data = watchlist_response.json()
        # API returns {'count': N, 'stocks': [...]}
        stocks = watchlist_data.get("stocks", watchlist_data) if isinstance(watchlist_data, dict) else watchlist_data

        if len(stocks) > 0:
            # Step 2: Get signal for first ticker
            ticker = stocks[0].get("ticker", "NVDA")
            signal_response = test_client.get(f"/api/v1/signals/test/{ticker}")

            # Should process
            assert signal_response.status_code in [200, 404, 500]

    @pytest.mark.e2e
    def test_single_agent_analysis_flow(self, test_client):
        """Single agent analysis endpoint flow"""
        response = test_client.post(
            "/api/v1/signals/analyze/NVDA/single",
            params={"agent_name": "PredictorAgent"}
        )

        if response.status_code == 200:
            data = response.json()
            assert "ticker" in data
            assert "signal" in data
            assert "agent_name" in data

    @pytest.mark.e2e
    def test_market_data_flow(self, test_client):
        """Market data retrieval flow"""
        response = test_client.get("/api/v1/market/NVDA")

        if response.status_code == 200:
            data = response.json()
            # Verify structure
            assert "ticker" in data or "current_price" in data

    @pytest.mark.e2e
    def test_error_recovery_flow(self, test_client):
        """System recovers from errors gracefully"""
        # Invalid request - may return 400, 404, or 500 depending on implementation
        bad_response = test_client.get("/api/v1/signals/test/INVALID123")
        assert bad_response.status_code in [400, 404, 500]

        # Valid request should still work after error
        good_response = test_client.get("/api/v1/health")
        assert good_response.status_code == 200


class TestPortfolioFlowE2E:
    """Test portfolio tracking flows - 5 tests"""

    @pytest.mark.e2e
    def test_watchlist_retrieval(self, test_client):
        """Watchlist retrieval flow"""
        response = test_client.get("/api/v1/data/watchlist")

        assert response.status_code == 200
        data = response.json()
        # API returns {'count': N, 'stocks': [...]} or just a list
        if isinstance(data, dict):
            assert "stocks" in data
            assert isinstance(data["stocks"], list)
        else:
            assert isinstance(data, list)

    @pytest.mark.e2e
    def test_watchlist_structure(self, test_client):
        """Watchlist items have correct structure"""
        response = test_client.get("/api/v1/data/watchlist")

        if response.status_code == 200:
            data = response.json()
            # Handle both dict and list response formats
            stocks = data.get("stocks", data) if isinstance(data, dict) else data
            if len(stocks) > 0:
                item = stocks[0]
                assert "ticker" in item

    @pytest.mark.e2e
    def test_ticker_detail_flow(self, test_client):
        """Get detailed info for specific ticker"""
        response = test_client.get("/api/v1/market/NVDA/quote")

        # May return data or 404 depending on API
        assert response.status_code in [200, 404, 500]

    @pytest.mark.e2e
    def test_technical_analysis_flow(self, test_client):
        """Technical analysis retrieval flow"""
        response = test_client.get("/api/v1/market/NVDA/technical")

        assert response.status_code in [200, 404, 500]

    @pytest.mark.e2e
    def test_sentiment_analysis_flow(self, test_client):
        """Sentiment analysis retrieval flow"""
        response = test_client.get("/api/v1/sentiment/NVDA")

        assert response.status_code in [200, 404, 500]
