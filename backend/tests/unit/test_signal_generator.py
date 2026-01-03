"""
Unit Tests for SignalGenerator
Tests consensus algorithm, weighted voting, and position sizing
"""

import pytest
from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.agents.rule_based_agent import RuleBasedAgent
from app.agents.signal_generator import (
    SignalGenerator,
    ConsensusSignal,
    PositionSize,
)


class MockAgent(BaseAgent):
    """Mock agent for testing with configurable responses"""

    def __init__(
        self,
        name: str = "MockAgent",
        weight: float = 1.0,
        signal_type: SignalType = SignalType.HOLD,
        confidence: float = 0.5,
        raw_score: float = 0.0,
    ):
        super().__init__(name=name, weight=weight)
        self._signal_type = signal_type
        self._confidence = confidence
        self._raw_score = raw_score

    def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
        return AgentSignal(
            agent_name=self.name,
            ticker=ticker,
            signal=self._signal_type,
            confidence=self._confidence,
            reasoning=f"{self.name} analysis",
            raw_score=self._raw_score,
        )


class TestPositionSize:
    """Tests for PositionSize enum"""

    def test_position_sizes_exist(self):
        """Test all position sizes are defined"""
        assert PositionSize.NONE.value == "NONE"
        assert PositionSize.SMALL.value == "SMALL"
        assert PositionSize.MEDIUM.value == "MEDIUM"
        assert PositionSize.NORMAL.value == "NORMAL"
        assert PositionSize.LARGE.value == "LARGE"


class TestConsensusSignal:
    """Tests for ConsensusSignal dataclass"""

    def test_consensus_creation(self):
        """Test basic consensus signal creation"""
        consensus = ConsensusSignal(
            ticker="NVDA",
            signal=SignalType.BUY,
            confidence=0.75,
            raw_score=0.4,
            position_size=PositionSize.NORMAL,
        )
        assert consensus.ticker == "NVDA"
        assert consensus.signal == SignalType.BUY
        assert consensus.confidence == 0.75
        assert consensus.position_size == PositionSize.NORMAL

    def test_consensus_to_dict(self):
        """Test consensus serialization"""
        consensus = ConsensusSignal(
            ticker="NVDA",
            signal=SignalType.BUY,
            confidence=0.75,
            raw_score=0.4,
            position_size=PositionSize.NORMAL,
            agreement_ratio=0.8,
            reasoning="Test reasoning",
        )
        result = consensus.to_dict()

        assert result["ticker"] == "NVDA"
        assert result["signal"] == "BUY"
        assert result["confidence"] == 0.75
        assert result["position_size"] == "NORMAL"
        assert result["agreement_ratio"] == 0.8


class TestSignalGenerator:
    """Tests for SignalGenerator class"""

    def test_generator_creation(self):
        """Test generator initialization"""
        generator = SignalGenerator()
        assert generator.agents == []

    def test_generator_with_agents(self):
        """Test initialization with agents"""
        agent = RuleBasedAgent()
        generator = SignalGenerator(agents=[agent])
        assert len(generator.agents) == 1

    def test_register_agent(self):
        """Test agent registration"""
        generator = SignalGenerator()
        agent = RuleBasedAgent(name="TestAgent")
        generator.register_agent(agent)

        assert len(generator.agents) == 1
        assert "TestAgent" in generator.get_agent_names()

    def test_register_duplicate_agent(self):
        """Test duplicate agent is not registered twice"""
        generator = SignalGenerator()
        agent = RuleBasedAgent(name="TestAgent")
        generator.register_agent(agent)
        generator.register_agent(agent)

        assert len(generator.agents) == 1

    def test_unregister_agent(self):
        """Test agent unregistration"""
        generator = SignalGenerator()
        agent = RuleBasedAgent(name="TestAgent")
        generator.register_agent(agent)

        result = generator.unregister_agent("TestAgent")
        assert result is True
        assert len(generator.agents) == 0

    def test_unregister_nonexistent_agent(self):
        """Test unregistering nonexistent agent"""
        generator = SignalGenerator()
        result = generator.unregister_agent("NonExistent")
        assert result is False

    def test_generate_signal_no_agents(self):
        """Test signal generation with no agents"""
        generator = SignalGenerator()
        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        assert consensus.signal == SignalType.HOLD
        assert consensus.confidence == 0.0
        assert consensus.position_size == PositionSize.NONE

    def test_generate_signal_invalid_input(self):
        """Test signal generation with invalid input"""
        generator = SignalGenerator(agents=[RuleBasedAgent()])
        consensus = generator.generate_signal(
            ticker="",
            market_data=None,
        )

        assert consensus.signal == SignalType.HOLD
        assert consensus.confidence == 0.0

    def test_generate_signal_single_agent_bullish(self):
        """Test signal with single bullish agent"""
        agent = MockAgent(
            name="Bullish",
            signal_type=SignalType.BUY,
            confidence=0.8,
            raw_score=0.5,
        )
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 30}},
        )

        assert consensus.signal == SignalType.BUY
        assert consensus.raw_score > 0

    def test_generate_signal_single_agent_bearish(self):
        """Test signal with single bearish agent"""
        agent = MockAgent(
            name="Bearish",
            signal_type=SignalType.SELL,
            confidence=0.8,
            raw_score=-0.5,
        )
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 70}},
        )

        assert consensus.signal == SignalType.SELL
        assert consensus.raw_score < 0

    def test_generate_signal_multiple_agents_agreement(self):
        """Test consensus with multiple agreeing agents"""
        agents = [
            MockAgent(name="Agent1", raw_score=0.6, confidence=0.8),
            MockAgent(name="Agent2", raw_score=0.5, confidence=0.7),
            MockAgent(name="Agent3", raw_score=0.4, confidence=0.6),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 30}},
        )

        assert consensus.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        assert consensus.agreement_ratio >= 0.8
        assert consensus.confidence > 0.5

    def test_generate_signal_multiple_agents_disagreement(self):
        """Test consensus with disagreeing agents"""
        agents = [
            MockAgent(name="Bull", raw_score=0.6, confidence=0.8),
            MockAgent(name="Bear", raw_score=-0.6, confidence=0.8),
            MockAgent(name="Neutral", raw_score=0.0, confidence=0.5),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        # With disagreement, should be closer to neutral
        assert consensus.agreement_ratio < 0.8
        assert consensus.position_size in [
            PositionSize.NONE,
            PositionSize.SMALL,
            PositionSize.MEDIUM,
        ]


class TestWeightedVoting:
    """Tests for weighted voting algorithm"""

    def test_higher_weight_agent_dominates(self):
        """Test that higher weight agents have more influence"""
        agents = [
            MockAgent(name="HighWeight", weight=2.0, raw_score=0.8, confidence=0.8),
            MockAgent(name="LowWeight", weight=0.5, raw_score=-0.8, confidence=0.8),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        # Higher weight bullish agent should dominate
        assert consensus.raw_score > 0

    def test_higher_confidence_has_more_weight(self):
        """Test that higher confidence signals have more influence"""
        agents = [
            MockAgent(name="HighConf", raw_score=0.5, confidence=0.9),
            MockAgent(name="LowConf", raw_score=-0.5, confidence=0.2),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        # Higher confidence bullish should dominate
        assert consensus.raw_score > 0

    def test_equal_weights_average(self):
        """Test that equal weights produce average"""
        agents = [
            MockAgent(name="Agent1", weight=1.0, raw_score=0.6, confidence=0.8),
            MockAgent(name="Agent2", weight=1.0, raw_score=0.4, confidence=0.8),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        # Should be approximately average of 0.6 and 0.4 = 0.5
        assert 0.4 <= consensus.raw_score <= 0.6


class TestPositionSizing:
    """Tests for position sizing calculation"""

    def test_no_position_low_confidence(self):
        """Test no position for low confidence with disagreement"""
        # Multiple disagreeing agents with low confidence = no position
        agents = [
            MockAgent(name="A1", raw_score=0.3, confidence=0.2),
            MockAgent(name="A2", raw_score=-0.3, confidence=0.2),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        # Low confidence + disagreement = no position
        assert consensus.position_size == PositionSize.NONE

    def test_no_position_weak_signal(self):
        """Test no position for weak signal"""
        agent = MockAgent(raw_score=0.1, confidence=0.8)
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        assert consensus.position_size == PositionSize.NONE

    def test_large_position_high_conviction(self):
        """Test large position for high conviction"""
        agents = [
            MockAgent(name="A1", raw_score=0.7, confidence=0.9),
            MockAgent(name="A2", raw_score=0.8, confidence=0.85),
            MockAgent(name="A3", raw_score=0.6, confidence=0.8),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 25}},
        )

        assert consensus.position_size == PositionSize.LARGE

    def test_normal_position_moderate_conviction(self):
        """Test normal position for moderate conviction"""
        agents = [
            MockAgent(name="A1", raw_score=0.5, confidence=0.6),
            MockAgent(name="A2", raw_score=0.4, confidence=0.6),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 35}},
        )

        assert consensus.position_size in [PositionSize.NORMAL, PositionSize.MEDIUM]


class TestAgreementCalculation:
    """Tests for agreement ratio calculation"""

    def test_full_agreement_bullish(self):
        """Test full agreement when all bullish"""
        agents = [
            MockAgent(name="A1", raw_score=0.5),
            MockAgent(name="A2", raw_score=0.6),
            MockAgent(name="A3", raw_score=0.4),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 30}},
        )

        assert consensus.agreement_ratio == 1.0

    def test_full_agreement_bearish(self):
        """Test full agreement when all bearish"""
        agents = [
            MockAgent(name="A1", raw_score=-0.5),
            MockAgent(name="A2", raw_score=-0.6),
            MockAgent(name="A3", raw_score=-0.4),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 70}},
        )

        assert consensus.agreement_ratio == 1.0

    def test_split_agreement(self):
        """Test 50/50 split agreement"""
        agents = [
            MockAgent(name="Bull1", raw_score=0.5),
            MockAgent(name="Bull2", raw_score=0.5),
            MockAgent(name="Bear1", raw_score=-0.5),
            MockAgent(name="Bear2", raw_score=-0.5),
        ]
        generator = SignalGenerator(agents=agents)

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        assert consensus.agreement_ratio == 0.5

    def test_single_agent_full_agreement(self):
        """Test single agent has full agreement"""
        agent = MockAgent(raw_score=0.5)
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 30}},
        )

        assert consensus.agreement_ratio == 1.0


class TestWithRuleBasedAgent:
    """Integration tests with actual RuleBasedAgent"""

    def test_bullish_scenario(self):
        """Test bullish market conditions"""
        agent = RuleBasedAgent()
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={
                "indicators": {
                    "rsi": 30,
                    "price_change_7d": 5.0,
                    "volume_trend": "increasing",
                }
            },
            sentiment_data={
                "combined_sentiment": 0.6,
                "total_mentions": 100,
            },
        )

        assert consensus.signal in [SignalType.BUY, SignalType.STRONG_BUY]
        assert consensus.raw_score > 0

    def test_bearish_scenario(self):
        """Test bearish market conditions"""
        agent = RuleBasedAgent()
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
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
                "total_mentions": 100,
            },
        )

        assert consensus.signal in [SignalType.SELL, SignalType.STRONG_SELL]
        assert consensus.raw_score < 0

    def test_neutral_scenario(self):
        """Test neutral market conditions"""
        agent = RuleBasedAgent()
        generator = SignalGenerator(agents=[agent])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 50}},
        )

        assert consensus.signal == SignalType.HOLD
        assert abs(consensus.raw_score) < 0.3


class TestErrorHandling:
    """Tests for error handling"""

    def test_agent_exception_handled(self):
        """Test that agent exceptions don't crash generator"""

        class FailingAgent(BaseAgent):
            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                raise ValueError("Agent failed")

        agents = [
            FailingAgent(name="Failing"),
            MockAgent(name="Working", raw_score=0.5, confidence=0.8),
        ]
        generator = SignalGenerator(agents=agents)

        # Should not raise, should use working agent
        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 30}},
        )

        assert len(consensus.agent_signals) == 1
        assert consensus.agent_signals[0].agent_name == "Working"

    def test_all_agents_fail(self):
        """Test when all agents fail"""

        class FailingAgent(BaseAgent):
            def analyze(self, ticker, market_data, sentiment_data=None, historical_data=None):
                raise ValueError("Agent failed")

        generator = SignalGenerator(agents=[FailingAgent(name="Failing")])

        consensus = generator.generate_signal(
            ticker="NVDA",
            market_data={"indicators": {"rsi": 30}},
        )

        assert consensus.signal == SignalType.HOLD
        assert consensus.confidence == 0.0


class TestRepr:
    """Tests for string representation"""

    def test_generator_repr(self):
        """Test generator string representation"""
        agents = [
            RuleBasedAgent(name="Agent1"),
            RuleBasedAgent(name="Agent2"),
        ]
        generator = SignalGenerator(agents=agents)

        repr_str = repr(generator)
        assert "SignalGenerator" in repr_str
        assert "Agent1" in repr_str
        assert "Agent2" in repr_str

    def test_empty_generator_repr(self):
        """Test empty generator representation"""
        generator = SignalGenerator()
        repr_str = repr(generator)
        assert "SignalGenerator" in repr_str
