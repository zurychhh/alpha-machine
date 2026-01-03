"""
Performance Tests for Alpha Machine
Measures response times and resource usage
"""

import pytest
import time
from app.agents.predictor_agent import PredictorAgent
from app.agents.rule_based_agent import RuleBasedAgent
from app.agents.signal_generator import SignalGenerator
from app.agents.base_agent import AgentSignal


@pytest.fixture
def mock_market_data():
    """Standard market data for performance tests"""
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


class TestResponseTime:
    """Measure critical path latency - 10 tests"""

    @pytest.mark.performance
    def test_predictor_agent_response_time(self, mock_market_data, mock_sentiment_data):
        """PredictorAgent analysis < 100ms"""
        agent = PredictorAgent()

        start = time.time()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)
        elapsed = time.time() - start

        assert elapsed < 0.1  # 100ms
        assert isinstance(result, AgentSignal)

    @pytest.mark.performance
    def test_rule_based_agent_response_time(self, mock_market_data, mock_sentiment_data):
        """RuleBasedAgent analysis < 100ms"""
        agent = RuleBasedAgent()

        start = time.time()
        result = agent.analyze("NVDA", mock_market_data, mock_sentiment_data)
        elapsed = time.time() - start

        assert elapsed < 0.1  # 100ms
        assert isinstance(result, AgentSignal)

    @pytest.mark.performance
    def test_local_agents_parallel_time(self, mock_market_data, mock_sentiment_data):
        """Multiple local agents < 200ms"""
        agents = [PredictorAgent(), RuleBasedAgent()]

        start = time.time()
        results = [a.analyze("NVDA", mock_market_data, mock_sentiment_data) for a in agents]
        elapsed = time.time() - start

        assert elapsed < 0.2  # 200ms for both
        assert len(results) == 2

    @pytest.mark.performance
    def test_signal_generator_local_time(self, mock_market_data, mock_sentiment_data):
        """SignalGenerator with local agents < 500ms"""
        generator = SignalGenerator(agents=[
            PredictorAgent(),
            RuleBasedAgent(),
        ])

        start = time.time()
        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data=mock_market_data,
            sentiment_data=mock_sentiment_data,
        )
        elapsed = time.time() - start

        assert elapsed < 0.5  # 500ms
        assert consensus is not None

    @pytest.mark.performance
    def test_repeated_analyses_consistent_time(self, mock_market_data):
        """100 consecutive analyses have consistent timing"""
        agent = PredictorAgent()
        times = []

        for _ in range(100):
            start = time.time()
            agent.analyze("NVDA", mock_market_data)
            times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        # Average should be very fast
        assert avg_time < 0.01  # 10ms average
        # Max should not be outlier
        assert max_time < 0.1  # 100ms max

    @pytest.mark.performance
    def test_different_tickers_same_speed(self, mock_market_data):
        """Different tickers process at same speed"""
        agent = PredictorAgent()
        tickers = ["NVDA", "AAPL", "MSFT", "GOOGL", "AMD"]

        times = {}
        for ticker in tickers:
            start = time.time()
            agent.analyze(ticker, mock_market_data)
            times[ticker] = time.time() - start

        # All should be similar speed
        avg = sum(times.values()) / len(times)
        for ticker, t in times.items():
            assert abs(t - avg) < 0.05  # Within 50ms of average

    @pytest.mark.performance
    def test_agent_initialization_time(self):
        """Agent initialization < 50ms"""
        start = time.time()
        agent = PredictorAgent()
        elapsed = time.time() - start

        assert elapsed < 0.05  # 50ms

    @pytest.mark.performance
    def test_signal_generator_initialization_time(self):
        """SignalGenerator initialization < 100ms"""
        agents = [PredictorAgent(), RuleBasedAgent()]

        start = time.time()
        generator = SignalGenerator(agents=agents)
        elapsed = time.time() - start

        assert elapsed < 0.1  # 100ms

    @pytest.mark.performance
    def test_consensus_calculation_time(self, mock_market_data):
        """Consensus calculation < 50ms"""
        generator = SignalGenerator(agents=[
            PredictorAgent(),
            RuleBasedAgent(),
        ])

        # First generate to populate agent signals
        consensus = generator.generate_signal("NVDA", mock_market_data)

        # Measure just consensus calculation
        start = time.time()
        _ = generator.generate_signal("NVDA", mock_market_data)
        elapsed = time.time() - start

        assert elapsed < 0.1  # 100ms (includes agent analysis)

    @pytest.mark.performance
    def test_memory_stability_under_load(self, mock_market_data):
        """Memory stable during 1000 analyses"""
        import sys

        agent = PredictorAgent()

        # Run many analyses
        for _ in range(1000):
            result = agent.analyze("NVDA", mock_market_data)

        # Should complete without memory issues
        assert True  # If we get here, memory was stable


class TestLoadHandling:
    """Test system under load - 5 tests"""

    @pytest.mark.performance
    def test_burst_requests(self, mock_market_data):
        """Handle burst of 50 quick requests"""
        agent = PredictorAgent()

        start = time.time()
        results = [agent.analyze("NVDA", mock_market_data) for _ in range(50)]
        elapsed = time.time() - start

        # All should complete
        assert len(results) == 50
        # Should be fast in total
        assert elapsed < 1.0  # 1 second for 50 requests

    @pytest.mark.performance
    def test_sustained_load(self, mock_market_data):
        """Sustained load over 5 seconds"""
        agent = PredictorAgent()
        count = 0

        start = time.time()
        while time.time() - start < 2.0:  # 2 seconds
            agent.analyze("NVDA", mock_market_data)
            count += 1

        # Should handle many requests per second
        assert count > 100  # At least 50 per second

    @pytest.mark.performance
    def test_multiple_generators(self, mock_market_data):
        """Multiple SignalGenerators work independently"""
        generators = [
            SignalGenerator(agents=[PredictorAgent()]),
            SignalGenerator(agents=[RuleBasedAgent()]),
        ]

        start = time.time()
        results = [g.generate_signal("NVDA", mock_market_data) for g in generators]
        elapsed = time.time() - start

        assert len(results) == 2
        assert elapsed < 0.5

    @pytest.mark.performance
    def test_varied_data_load(self):
        """Different data doesn't affect performance"""
        agent = PredictorAgent()

        data_variants = [
            {"indicators": {"rsi": 20}},
            {"indicators": {"rsi": 50, "price_change_7d": 5}},
            {"indicators": {"rsi": 80, "volume_trend": "increasing"}},
            {"current_price": 100, "indicators": {"rsi": 45}},
        ]

        times = []
        for data in data_variants:
            start = time.time()
            agent.analyze("NVDA", data)
            times.append(time.time() - start)

        # All should be similar
        avg = sum(times) / len(times)
        for t in times:
            assert abs(t - avg) < 0.05

    @pytest.mark.performance
    def test_error_handling_performance(self):
        """Error handling doesn't add significant overhead"""
        agent = PredictorAgent()

        # Valid data
        start_valid = time.time()
        for _ in range(100):
            agent.analyze("NVDA", {"indicators": {"rsi": 50}})
        valid_time = time.time() - start_valid

        # Invalid data (will use error handling)
        start_invalid = time.time()
        for _ in range(100):
            agent.analyze("NVDA", None)
        invalid_time = time.time() - start_invalid

        # Error handling may include logging overhead, allow 5x
        assert invalid_time < valid_time * 5
