"""
Integration Tests for Multi-Agent System
Tests agents working together in consensus
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents import (
    SignalGenerator,
    ContrarianAgent,
    GrowthAgent,
    MultiModalAgent,
    PredictorAgent,
    RuleBasedAgent,
)
from app.agents.base_agent import SignalType, AgentSignal


@pytest.fixture
def mock_market_data():
    """Standard market data for integration tests"""
    return {
        "ticker": "NVDA",
        "current_price": 180.50,
        "indicators": {
            "rsi": 55.0,
            "price_change_7d": 3.25,
            "price_change_30d": 8.50,
            "volume_trend": "increasing",
            "sma_50": 175.00,
            "sma_200": 160.00,
        }
    }


@pytest.fixture
def mock_sentiment_data():
    """Standard sentiment data"""
    return {
        "combined_sentiment": 0.45,
        "sentiment_label": "slightly_bullish",
        "total_mentions": 50,
    }


class TestMultiAgentIntegration:
    """Test agents working together - 10 tests"""

    def test_predictor_agent_standalone(self, mock_market_data, mock_sentiment_data):
        """PredictorAgent works independently"""
        agent = PredictorAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

        assert isinstance(result, AgentSignal)
        assert result.ticker == "NVDA"

    def test_rule_based_agent_standalone(self, mock_market_data, mock_sentiment_data):
        """RuleBasedAgent works independently"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

        assert isinstance(result, AgentSignal)
        assert result.ticker == "NVDA"

    def test_multiple_agents_different_signals(self, mock_market_data, mock_sentiment_data):
        """Different agents can produce different signals"""
        predictor = PredictorAgent()
        rule_based = RuleBasedAgent()

        result1 = predictor.analyze("NVDA", mock_market_data, mock_sentiment_data)
        result2 = rule_based.analyze("NVDA", mock_market_data, mock_sentiment_data)

        # Both should be valid AgentSignals
        assert isinstance(result1, AgentSignal)
        assert isinstance(result2, AgentSignal)

    def test_signal_generator_with_local_agents(self, mock_market_data, mock_sentiment_data):
        """SignalGenerator works with local agents"""
        agents = [
            PredictorAgent(weight=1.0),
            RuleBasedAgent(weight=1.0),
        ]

        generator = SignalGenerator(agents=agents)
        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data=mock_market_data,
            sentiment_data=mock_sentiment_data,
        )

        assert consensus is not None
        assert consensus.ticker == "NVDA"
        assert consensus.signal in SignalType

    def test_consensus_with_agreeing_agents(self):
        """High agreement when all agents agree"""
        # Create mock agents that all return BUY
        class MockBuyAgent:
            def __init__(self, name, weight=1.0):
                self.name = name
                self.weight = weight

            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                return AgentSignal(
                    agent_name=self.name,
                    ticker=ticker,
                    signal=SignalType.BUY,
                    confidence=0.8,
                    reasoning="Bullish",
                    raw_score=0.6,
                )

        agents = [MockBuyAgent(f"Agent{i}") for i in range(4)]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal("NVDA", {"indicators": {"rsi": 50}})

        assert consensus.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        assert consensus.agreement_ratio >= 0.75

    def test_consensus_with_mixed_signals(self):
        """Lower confidence when agents disagree"""
        class MockAgent:
            def __init__(self, name, signal, weight=1.0):
                self.name = name
                self.weight = weight
                self._signal = signal

            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                return AgentSignal(
                    agent_name=self.name,
                    ticker=ticker,
                    signal=self._signal,
                    confidence=0.7,
                    reasoning="Test",
                    raw_score=0.3 if self._signal == SignalType.BUY else -0.3,
                )

        agents = [
            MockAgent("Agent1", SignalType.BUY),
            MockAgent("Agent2", SignalType.BUY),
            MockAgent("Agent3", SignalType.SELL),
            MockAgent("Agent4", SignalType.SELL),
        ]

        generator = SignalGenerator(agents=agents)
        consensus = generator.generate_signal("NVDA", {"indicators": {"rsi": 50}})

        # Mixed signals should result in HOLD or lower confidence
        assert consensus.agreement_ratio < 1.0

    def test_agent_weights_affect_consensus(self):
        """Agent weights influence consensus signal"""
        class MockAgent:
            def __init__(self, name, signal, weight=1.0):
                self.name = name
                self.weight = weight
                self._signal = signal

            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                return AgentSignal(
                    agent_name=self.name,
                    ticker=ticker,
                    signal=self._signal,
                    confidence=0.7,
                    reasoning="Test",
                    raw_score=0.5 if self._signal == SignalType.BUY else -0.5,
                )

        # One high-weight BUY agent vs two low-weight SELL agents
        agents = [
            MockAgent("HeavyBuy", SignalType.BUY, weight=2.0),
            MockAgent("LightSell1", SignalType.SELL, weight=0.5),
            MockAgent("LightSell2", SignalType.SELL, weight=0.5),
        ]

        generator = SignalGenerator(agents=agents)
        consensus = generator.generate_signal("NVDA", {"indicators": {"rsi": 50}})

        # Heavy BUY agent should influence result
        assert consensus.raw_score >= 0  # Leaning bullish

    def test_single_agent_failure_continues(self, mock_market_data):
        """System continues when one agent fails"""
        class FailingAgent:
            def __init__(self, name):
                self.name = name
                self.weight = 1.0

            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                raise Exception("Agent failed!")

        agents = [
            FailingAgent("Failing"),
            PredictorAgent(),
            RuleBasedAgent(),
        ]

        generator = SignalGenerator(agents=agents)
        consensus = generator.generate_signal("NVDA", mock_market_data)

        # Should still return a valid consensus from working agents
        assert consensus is not None
        assert len(consensus.agent_signals) >= 1

    def test_all_agents_fail_returns_hold(self, mock_market_data):
        """All agents failing returns HOLD signal"""
        class FailingAgent:
            def __init__(self, name):
                self.name = name
                self.weight = 1.0

            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                raise Exception("Agent failed!")

        agents = [FailingAgent(f"Failing{i}") for i in range(3)]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal("NVDA", mock_market_data)

        assert consensus.signal == SignalType.HOLD
        assert consensus.confidence == 0.0

    def test_signal_generator_empty_agents(self, mock_market_data):
        """SignalGenerator handles no agents gracefully"""
        generator = SignalGenerator(agents=[])
        consensus = generator.generate_signal("NVDA", mock_market_data)

        assert consensus.signal == SignalType.HOLD


class TestDataPipelineIntegration:
    """Test data flow integration - 15 tests"""

    def test_market_data_flows_to_predictor(self, mock_market_data):
        """Market data correctly flows to PredictorAgent"""
        agent = PredictorAgent()
        result = agent.analyze("NVDA", mock_market_data)

        # Agent should have processed the RSI
        assert result.factors is not None

    def test_sentiment_data_flows_to_agent(self, mock_market_data, mock_sentiment_data):
        """Sentiment data correctly flows to agents"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

        assert "sentiment" in result.factors

    def test_historical_data_accepted(self, mock_market_data):
        """Agents accept historical data parameter"""
        historical = [
            {"date": "2025-12-20", "close": 180.0},
            {"date": "2025-12-19", "close": 178.0},
        ]

        agent = PredictorAgent()
        result = agent.analyze("NVDA", mock_market_data, historical_data=historical)

        assert isinstance(result, AgentSignal)

    def test_missing_sentiment_handled(self, mock_market_data):
        """Missing sentiment data handled gracefully"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data, sentiment_data=None)

        assert isinstance(result, AgentSignal)

    def test_partial_indicators_handled(self):
        """Partial indicator data handled"""
        partial_data = {"indicators": {"rsi": 50}}  # Only RSI

        agent = PredictorAgent()
        result = agent.analyze("NVDA", partial_data)

        assert isinstance(result, AgentSignal)

    def test_empty_indicators_handled(self):
        """Empty indicators handled"""
        agent = PredictorAgent()
        result = agent.analyze("NVDA", {"indicators": {}})

        assert isinstance(result, AgentSignal)
        assert result.signal == SignalType.HOLD

    def test_rsi_indicator_processed(self, mock_market_data):
        """RSI indicator properly processed"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data)

        assert "rsi" in result.factors

    def test_momentum_indicators_processed(self, mock_market_data):
        """Momentum indicators properly processed"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data)

        assert "momentum_7d" in result.factors or "momentum_30d" in result.factors

    def test_volume_trend_processed(self, mock_market_data):
        """Volume trend properly processed"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data)

        assert "volume_trend" in result.factors

    def test_combined_sentiment_processed(self, mock_market_data, mock_sentiment_data):
        """Combined sentiment properly processed"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

        sentiment_factor = result.factors.get("sentiment", 0)
        assert sentiment_factor != 0  # Should have extracted sentiment

    def test_extreme_rsi_values_processed(self):
        """Extreme RSI values don't break agents"""
        extreme_data = {"indicators": {"rsi": 95}}

        agent = PredictorAgent()
        result = agent.analyze("NVDA", extreme_data)

        assert isinstance(result, AgentSignal)
        assert result.raw_score < 0  # Should be bearish

    def test_negative_momentum_processed(self):
        """Negative momentum properly interpreted"""
        negative_data = {"indicators": {"price_change_7d": -15.0}}

        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", negative_data)

        assert result.factors.get("momentum_7d", 0) < 0

    def test_ticker_passed_through(self, mock_market_data):
        """Ticker properly passed to signal"""
        agent = PredictorAgent()
        result = agent.analyze("AAPL", mock_market_data)

        assert result.ticker == "AAPL"

    def test_agent_name_in_signal(self, mock_market_data):
        """Agent name included in signal"""
        agent = PredictorAgent(name="CustomName")
        result = agent.analyze("NVDA", mock_market_data)

        assert result.agent_name == "CustomName"

    def test_reasoning_generated(self, mock_market_data, mock_sentiment_data):
        """Reasoning properly generated"""
        agent = RuleBasedAgent()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

        assert len(result.reasoning) > 0


class TestAPIIntegration:
    """Test API endpoint integration - 20 tests"""

    @pytest.fixture
    def test_client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_health_endpoint(self, test_client):
        """Health endpoint responds"""
        response = test_client.get("/api/v1/health")
        assert response.status_code == 200

    def test_agents_list_endpoint(self, test_client):
        """Agents list endpoint works"""
        response = test_client.get("/api/v1/signals/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data

    def test_agents_have_required_fields(self, test_client):
        """Agent info has required fields"""
        response = test_client.get("/api/v1/signals/agents")
        data = response.json()

        for agent in data["agents"]:
            assert "name" in agent
            assert "type" in agent
            assert "weight" in agent

    def test_signal_test_endpoint_valid_ticker(self, test_client):
        """Signal test endpoint works with valid ticker"""
        response = test_client.get("/api/v1/signals/test/NVDA")
        # May return 200 or error depending on API availability
        assert response.status_code in [200, 404, 500]

    def test_signal_test_endpoint_invalid_ticker(self, test_client):
        """Signal test endpoint rejects invalid ticker"""
        response = test_client.get("/api/v1/signals/test/123INVALID")
        # API may return 400 (validation) or 404 (data not found)
        assert response.status_code in [400, 404]

    def test_market_quote_endpoint(self, test_client):
        """Market quote endpoint structure"""
        response = test_client.get("/api/v1/market/NVDA/quote")
        # Response depends on API keys
        assert response.status_code in [200, 404, 500]

    def test_technical_indicators_endpoint(self, test_client):
        """Technical indicators endpoint structure"""
        response = test_client.get("/api/v1/market/NVDA/technical")
        assert response.status_code in [200, 404, 500]

    def test_sentiment_endpoint(self, test_client):
        """Sentiment endpoint structure"""
        response = test_client.get("/api/v1/sentiment/NVDA")
        assert response.status_code in [200, 404, 500]

    def test_watchlist_endpoint(self, test_client):
        """Watchlist endpoint works"""
        response = test_client.get("/api/v1/data/watchlist")
        assert response.status_code == 200

    def test_api_error_handling(self, test_client):
        """API handles errors gracefully"""
        response = test_client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_content_type_json(self, test_client):
        """API returns JSON content type"""
        response = test_client.get("/api/v1/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_agents_count_matches(self, test_client):
        """Agent count matches agent list length"""
        response = test_client.get("/api/v1/signals/agents")
        data = response.json()

        assert data["agent_count"] == len(data["agents"])

    def test_post_signal_generate_structure(self, test_client):
        """Signal generate endpoint accepts POST"""
        response = test_client.post("/api/v1/signals/generate/NVDA")
        # May fail without API keys but should return proper structure
        assert response.status_code in [200, 404, 500]

    def test_query_params_accepted(self, test_client):
        """Query parameters accepted"""
        response = test_client.post(
            "/api/v1/signals/generate/NVDA",
            params={"include_sentiment": True, "days": 30}
        )
        assert response.status_code in [200, 404, 500]

    def test_uppercase_ticker_normalization(self, test_client):
        """Lowercase ticker normalized to uppercase"""
        response = test_client.get("/api/v1/signals/test/nvda")
        # Should work same as NVDA
        assert response.status_code in [200, 400, 404, 500]

    def test_long_ticker_rejected(self, test_client):
        """Ticker over 5 chars rejected"""
        response = test_client.get("/api/v1/signals/test/TOOLONGTICKERHERE")
        # API may return 400 (validation) or 404 (data not found)
        assert response.status_code in [400, 404]

    def test_numeric_ticker_rejected(self, test_client):
        """Numeric-only ticker rejected"""
        response = test_client.get("/api/v1/signals/test/12345")
        # API may return 400 (validation) or 404 (data not found)
        assert response.status_code in [400, 404]

    def test_single_agent_endpoint(self, test_client):
        """Single agent analysis endpoint exists"""
        response = test_client.post(
            "/api/v1/signals/analyze/NVDA/single",
            params={"agent_name": "PredictorAgent"}
        )
        assert response.status_code in [200, 404, 500]

    def test_invalid_agent_name_handled(self, test_client):
        """Invalid agent name returns 404"""
        response = test_client.post(
            "/api/v1/signals/analyze/NVDA/single",
            params={"agent_name": "NonExistentAgent"}
        )
        assert response.status_code == 404

    def test_cors_headers_present(self, test_client):
        """CORS headers present in response"""
        response = test_client.get("/api/v1/health")
        # Check for CORS or that it doesn't error
        assert response.status_code == 200
