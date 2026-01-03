"""
Unit Tests for AI Agent Framework
Tests BaseAgent, AgentSignal, and RuleBasedAgent
"""

import pytest
from datetime import datetime
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.agents.rule_based_agent import RuleBasedAgent


class TestSignalType:
    """Tests for SignalType enum"""

    def test_signal_types_exist(self):
        """Test all signal types are defined"""
        assert SignalType.STRONG_BUY.value == "STRONG_BUY"
        assert SignalType.BUY.value == "BUY"
        assert SignalType.HOLD.value == "HOLD"
        assert SignalType.SELL.value == "SELL"
        assert SignalType.STRONG_SELL.value == "STRONG_SELL"


class TestAgentSignal:
    """Tests for AgentSignal dataclass"""

    def test_signal_creation(self):
        """Test basic signal creation"""
        signal = AgentSignal(
            agent_name="TestAgent",
            ticker="NVDA",
            signal=SignalType.BUY,
            confidence=0.75,
            reasoning="Test reasoning",
        )
        assert signal.agent_name == "TestAgent"
        assert signal.ticker == "NVDA"
        assert signal.signal == SignalType.BUY
        assert signal.confidence == 0.75

    def test_signal_to_dict(self):
        """Test signal serialization"""
        signal = AgentSignal(
            agent_name="TestAgent",
            ticker="NVDA",
            signal=SignalType.BUY,
            confidence=0.75,
            reasoning="Test reasoning",
            factors={"rsi": 0.5},
            raw_score=0.4,
        )
        result = signal.to_dict()

        assert result["agent_name"] == "TestAgent"
        assert result["signal"] == "BUY"
        assert result["confidence"] == 0.75
        assert result["factors"]["rsi"] == 0.5

    def test_signal_from_score_strong_buy(self):
        """Test signal creation from high positive score"""
        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=0.8,
            confidence=0.9,
            reasoning="Very bullish",
        )
        assert signal.signal == SignalType.STRONG_BUY

    def test_signal_from_score_buy(self):
        """Test signal creation from moderate positive score"""
        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=0.4,
            confidence=0.7,
            reasoning="Bullish",
        )
        assert signal.signal == SignalType.BUY

    def test_signal_from_score_hold(self):
        """Test signal creation from neutral score"""
        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=0.0,
            confidence=0.5,
            reasoning="Neutral",
        )
        assert signal.signal == SignalType.HOLD

    def test_signal_from_score_sell(self):
        """Test signal creation from moderate negative score"""
        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=-0.4,
            confidence=0.7,
            reasoning="Bearish",
        )
        assert signal.signal == SignalType.SELL

    def test_signal_from_score_strong_sell(self):
        """Test signal creation from high negative score"""
        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=-0.8,
            confidence=0.9,
            reasoning="Very bearish",
        )
        assert signal.signal == SignalType.STRONG_SELL

    def test_score_clamping(self):
        """Test score is clamped to valid range"""
        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=1.5,  # Above max
            confidence=0.9,
            reasoning="Test",
        )
        assert signal.raw_score == 1.0

        signal = AgentSignal.from_score(
            agent_name="TestAgent",
            ticker="NVDA",
            score=-1.5,  # Below min
            confidence=0.9,
            reasoning="Test",
        )
        assert signal.raw_score == -1.0


class TestRuleBasedAgent:
    """Tests for RuleBasedAgent"""

    def test_agent_creation(self):
        """Test agent initialization"""
        agent = RuleBasedAgent(name="TestAgent", weight=0.8)
        assert agent.name == "TestAgent"
        assert agent.weight == 0.8

    def test_analyze_bullish_rsi(self):
        """Test bullish signal from oversold RSI"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 25}},
        )
        assert signal.raw_score > 0
        assert "oversold" in signal.reasoning.lower()

    def test_analyze_bearish_rsi(self):
        """Test bearish signal from overbought RSI"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 80}},
        )
        assert signal.raw_score < 0
        assert "overbought" in signal.reasoning.lower()

    def test_analyze_neutral_rsi(self):
        """Test neutral signal from neutral RSI"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )
        assert abs(signal.raw_score) < 0.3  # Near neutral

    def test_analyze_with_momentum(self):
        """Test signal incorporates momentum"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 50,
                    "price_change_7d": 10.0,  # Strong positive momentum
                }
            },
        )
        assert signal.raw_score > 0
        assert "momentum" in signal.reasoning.lower()

    def test_analyze_with_sentiment(self):
        """Test signal incorporates sentiment"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
            sentiment_data={
                "combined_sentiment": 0.7,
                "sentiment_label": "bullish",
                "total_mentions": 100,
            },
        )
        assert signal.raw_score > 0
        assert "sentiment" in signal.reasoning.lower()

    def test_analyze_with_volume(self):
        """Test signal incorporates volume trend"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 55,
                    "price_change_7d": 5.0,
                    "volume_trend": "increasing",
                }
            },
        )
        assert signal.factors["volume_trend"] > 0

    def test_analyze_comprehensive(self):
        """Test comprehensive bullish scenario"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 35,
                    "price_change_7d": 5.0,
                    "price_change_30d": 10.0,
                    "volume_trend": "increasing",
                }
            },
            sentiment_data={
                "combined_sentiment": 0.5,
                "sentiment_label": "bullish",
                "total_mentions": 50,
            },
        )
        assert signal.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        assert signal.confidence > 0.3

    def test_analyze_bearish_scenario(self):
        """Test comprehensive bearish scenario"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 75,
                    "price_change_7d": -8.0,
                    "volume_trend": "decreasing",
                }
            },
            sentiment_data={
                "combined_sentiment": -0.6,
                "sentiment_label": "bearish",
                "total_mentions": 100,
            },
        )
        assert signal.signal in [SignalType.SELL, SignalType.STRONG_SELL]
        assert signal.raw_score < 0

    def test_invalid_ticker(self):
        """Test handling of invalid ticker"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="",
            market_data={"indicators": {"rsi": 50}},
        )
        assert signal.signal == SignalType.HOLD
        assert signal.confidence == 0.0

    def test_invalid_market_data(self):
        """Test handling of invalid market data"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data=None,
        )
        assert signal.signal == SignalType.HOLD
        assert signal.confidence == 0.0

    def test_missing_indicators(self):
        """Test handling of missing indicators"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={},
        )
        # Should produce neutral signal with low confidence
        assert signal.signal == SignalType.HOLD
        assert signal.confidence < 0.3

    def test_custom_weights(self):
        """Test custom factor weights"""
        custom_weights = {
            "rsi": 0.5,  # Give RSI more weight
            "momentum_7d": 0.1,
            "momentum_30d": 0.1,
            "volume_trend": 0.1,
            "sentiment": 0.2,
        }
        agent = RuleBasedAgent(factor_weights=custom_weights)

        signal = agent.analyze(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 25}},  # Very oversold
        )

        # With higher RSI weight, should produce stronger bullish signal
        assert signal.raw_score > 0.3

    def test_factors_in_signal(self):
        """Test that all factors are included in signal"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 50,
                    "price_change_7d": 3.0,
                    "price_change_30d": 8.0,
                    "volume_trend": "increasing",
                }
            },
            sentiment_data={"combined_sentiment": 0.3, "total_mentions": 20},
        )

        assert "rsi" in signal.factors
        assert "momentum_7d" in signal.factors
        assert "momentum_30d" in signal.factors
        assert "volume_trend" in signal.factors
        assert "sentiment" in signal.factors

    def test_agent_repr(self):
        """Test agent string representation"""
        agent = RuleBasedAgent(name="TestAgent", weight=0.8)
        repr_str = repr(agent)

        assert "RuleBasedAgent" in repr_str
        assert "TestAgent" in repr_str
        assert "0.8" in repr_str


class TestConfidenceCalculation:
    """Tests for confidence calculation logic"""

    def test_high_confidence_agreement(self):
        """Test high confidence when factors agree"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 30,  # Bullish
                    "price_change_7d": 8.0,  # Bullish
                    "volume_trend": "increasing",  # Bullish
                }
            },
            sentiment_data={"combined_sentiment": 0.6, "total_mentions": 50},  # Bullish
        )
        assert signal.confidence > 0.5

    def test_low_confidence_disagreement(self):
        """Test lower confidence when factors disagree"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 30,  # Bullish
                    "price_change_7d": -5.0,  # Bearish
                }
            },
            sentiment_data={"combined_sentiment": -0.4, "total_mentions": 50},  # Bearish
        )
        # Mixed signals should have lower confidence than unanimous signals
        assert signal.confidence < 0.8

    def test_low_confidence_missing_data(self):
        """Test low confidence when data is missing"""
        agent = RuleBasedAgent()
        signal = agent.analyze(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )
        # Only RSI available, low data confidence
        assert signal.confidence < 0.5
