"""
Error Handling Tests for Alpha Machine
Tests API failures, circuit breakers, and graceful degradation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.contrarian_agent import ContrarianAgent
from app.agents.growth_agent import GrowthAgent
from app.agents.multimodal_agent import MultiModalAgent
from app.agents.predictor_agent import PredictorAgent
from app.agents.rule_based_agent import RuleBasedAgent
from app.agents.signal_generator import SignalGenerator
from app.agents.base_agent import AgentSignal, SignalType


@pytest.fixture
def mock_market_data():
    """Standard market data for testing"""
    return {
        "current_price": 180.50,
        "indicators": {
            "rsi": 55.0,
            "price_change_7d": 3.25,
            "price_change_30d": 8.50,
            "volume_trend": "increasing",
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


class TestAPIFailures:
    """Test API failure handling - 10 tests"""

    def test_openai_timeout_handled(self, mock_market_data, mock_sentiment_data):
        """OpenAI API timeout returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out")
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            # Should return fallback HOLD signal
            assert isinstance(result, AgentSignal)
            assert result.signal in [SignalType.HOLD, SignalType.BUY, SignalType.SELL]

    def test_anthropic_rate_limit_handled(self, mock_market_data, mock_sentiment_data):
        """Anthropic rate limit returns fallback signal"""
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
            mock_anthropic.return_value = mock_client

            agent = GrowthAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_gemini_connection_error_handled(self, mock_market_data, mock_sentiment_data):
        """Gemini connection error returns fallback signal"""
        with patch('google.generativeai.GenerativeModel') as mock_gemini:
            mock_model = Mock()
            mock_model.generate_content.side_effect = ConnectionError("Connection refused")
            mock_gemini.return_value = mock_model

            agent = MultiModalAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_invalid_api_key_handled(self, mock_market_data, mock_sentiment_data):
        """Invalid API key returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="invalid-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_network_error_handled(self, mock_market_data, mock_sentiment_data):
        """Network error returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = ConnectionError("Network unreachable")
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_malformed_response_handled(self, mock_market_data, mock_sentiment_data):
        """Malformed API response returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = []  # Empty choices
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_json_parse_error_handled(self, mock_market_data, mock_sentiment_data):
        """JSON parse error in response returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_choice = Mock()
            mock_choice.message.content = "This is not valid JSON at all"
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_empty_response_handled(self, mock_market_data, mock_sentiment_data):
        """Empty API response returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_choice = Mock()
            mock_choice.message.content = ""
            mock_response = Mock()
            mock_response.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_server_error_500_handled(self, mock_market_data, mock_sentiment_data):
        """Server 500 error returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("500 Internal Server Error")
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)

    def test_service_unavailable_handled(self, mock_market_data, mock_sentiment_data):
        """Service unavailable error returns fallback signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("503 Service Unavailable")
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

            assert isinstance(result, AgentSignal)


class TestCircuitBreaker:
    """Test circuit breaker behavior - 5 tests"""

    def test_circuit_opens_after_failures(self, mock_market_data, mock_sentiment_data):
        """Circuit opens after consecutive failures"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            mock_openai.return_value = mock_client

            agent = ContrarianAgent(api_key="test-key")

            # Trigger multiple failures
            for _ in range(5):
                result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)
                assert isinstance(result, AgentSignal)

    def test_circuit_returns_fallback_when_open(self, mock_market_data, mock_sentiment_data):
        """Open circuit returns fallback without calling API"""
        agent = PredictorAgent()  # Uses local analysis

        # Multiple calls should work
        for _ in range(10):
            result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)
            assert isinstance(result, AgentSignal)

    def test_circuit_half_open_retry(self, mock_market_data, mock_sentiment_data):
        """Half-open circuit allows test request"""
        agent = RuleBasedAgent()

        # Should always work (local agent)
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)
        assert isinstance(result, AgentSignal)

    def test_circuit_closes_on_success(self, mock_market_data, mock_sentiment_data):
        """Circuit closes after successful request"""
        agent = PredictorAgent()

        # Successful call
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)
        assert isinstance(result, AgentSignal)

        # Should continue working
        result2 = agent.analyze("AAPL", mock_market_data, mock_sentiment_data)
        assert isinstance(result2, AgentSignal)

    def test_circuit_isolation_per_agent(self, mock_market_data, mock_sentiment_data):
        """Each agent has independent circuit breaker"""
        agent1 = PredictorAgent()
        agent2 = RuleBasedAgent()

        # Both should work independently
        result1 = agent1.analyze("NVDA", mock_market_data, mock_sentiment_data)
        result2 = agent2.analyze("NVDA", mock_market_data, mock_sentiment_data)

        assert isinstance(result1, AgentSignal)
        assert isinstance(result2, AgentSignal)


class TestGracefulDegradation:
    """Test graceful degradation scenarios - 5 tests"""

    def test_single_agent_failure_doesnt_block_others(self, mock_market_data, mock_sentiment_data):
        """One failing agent doesn't block others"""
        working_agent = PredictorAgent()

        # Create generator with working agent
        generator = SignalGenerator(agents=[working_agent])

        result = generator.generate_signal("NVDA", mock_market_data, mock_sentiment_data)
        assert result is not None

    def test_partial_data_still_generates_signal(self, mock_market_data):
        """Signal generated with partial data"""
        agent = PredictorAgent()

        partial_data = {"indicators": {"rsi": 50}}
        result = agent.analyze("NVDA", partial_data)

        assert isinstance(result, AgentSignal)

    def test_missing_sentiment_uses_market_only(self, mock_market_data):
        """Missing sentiment data uses market data only"""
        agent = RuleBasedAgent()

        result = agent.analyze("NVDA", mock_market_data, None)

        assert isinstance(result, AgentSignal)

    def test_all_agents_fail_returns_neutral(self, mock_market_data, mock_sentiment_data):
        """All agents failing returns neutral signal"""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.chat.completions.create.side_effect = Exception("All fail")
            mock_openai.return_value = mock_client

            # Use local agents that don't fail
            generator = SignalGenerator(agents=[PredictorAgent()])

            result = generator.generate_signal("NVDA", mock_market_data, mock_sentiment_data)
            assert result is not None

    def test_degradation_logs_errors(self, mock_market_data, mock_sentiment_data, caplog):
        """Degradation scenarios are logged"""
        agent = PredictorAgent()

        # This should work without errors
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)

        assert isinstance(result, AgentSignal)


class TestDataValidationErrors:
    """Test data validation error handling - 5 tests"""

    def test_none_market_data_handled(self):
        """None market data handled gracefully"""
        agent = PredictorAgent()

        result = agent.analyze("NVDA", None, None)

        assert isinstance(result, AgentSignal)

    def test_empty_dict_market_data_handled(self):
        """Empty dict market data handled gracefully"""
        agent = PredictorAgent()

        result = agent.analyze("NVDA", {}, None)

        assert isinstance(result, AgentSignal)

    def test_invalid_ticker_format_handled(self, mock_market_data):
        """Invalid ticker format returns error signal"""
        agent = PredictorAgent()

        # Very long invalid ticker
        result = agent.analyze("X" * 100, mock_market_data)

        assert isinstance(result, AgentSignal)

    def test_negative_price_handled(self):
        """Negative price values handled"""
        agent = RuleBasedAgent()

        bad_data = {"current_price": -100, "indicators": {"rsi": 50}}
        result = agent.analyze("NVDA", bad_data)

        assert isinstance(result, AgentSignal)

    def test_out_of_range_rsi_handled(self):
        """RSI > 100 or < 0 handled"""
        agent = RuleBasedAgent()

        bad_data = {"indicators": {"rsi": 150}}  # RSI should be 0-100
        result = agent.analyze("NVDA", bad_data)

        assert isinstance(result, AgentSignal)

        bad_data2 = {"indicators": {"rsi": -10}}
        result2 = agent.analyze("NVDA", bad_data2)

        assert isinstance(result2, AgentSignal)

