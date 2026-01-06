"""
Signal Generator - Consensus Algorithm
Aggregates signals from multiple agents using weighted voting.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from app.agents.base_agent import BaseAgent, AgentSignal, SignalType

logger = logging.getLogger(__name__)


class PositionSize(Enum):
    """Position sizing recommendations"""

    NONE = "NONE"
    SMALL = "SMALL"  # 25% of normal position
    MEDIUM = "MEDIUM"  # 50% of normal position
    NORMAL = "NORMAL"  # 100% of normal position
    LARGE = "LARGE"  # 150% of normal position


@dataclass
class ConsensusSignal:
    """
    Aggregated signal from multiple agents.

    Attributes:
        ticker: Stock ticker symbol
        signal: Final consensus signal type
        confidence: Overall confidence (0.0 to 1.0)
        raw_score: Weighted average score (-1.0 to 1.0)
        position_size: Recommended position sizing
        agent_signals: Individual signals from each agent
        agreement_ratio: How much agents agree (0.0 to 1.0)
        reasoning: Summary of consensus reasoning
        timestamp: When the consensus was generated
    """

    ticker: str
    signal: SignalType
    confidence: float
    raw_score: float
    position_size: PositionSize
    agent_signals: List[AgentSignal] = field(default_factory=list)
    agreement_ratio: float = 0.0
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "ticker": self.ticker,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 3),
            "raw_score": round(self.raw_score, 3),
            "position_size": self.position_size.value,
            "agreement_ratio": round(self.agreement_ratio, 3),
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "agent_count": len(self.agent_signals),
            "agent_signals": [s.to_dict() for s in self.agent_signals],
        }


class SignalGenerator:
    """
    Generates consensus trading signals from multiple agents.

    Uses a weighted voting algorithm to combine signals from different
    analysis perspectives (technical, sentiment, fundamental, etc.)

    The consensus process:
    1. Collect signals from all registered agents
    2. Weight each signal by agent weight and confidence
    3. Calculate weighted average score
    4. Determine agreement ratio among agents
    5. Calculate position size based on confidence and agreement
    6. Generate final consensus signal
    """

    # Thresholds for position sizing
    HIGH_CONFIDENCE_THRESHOLD = 0.7
    MEDIUM_CONFIDENCE_THRESHOLD = 0.5
    LOW_CONFIDENCE_THRESHOLD = 0.3

    # Minimum agreement for strong positions
    MIN_AGREEMENT_FOR_LARGE = 0.8
    MIN_AGREEMENT_FOR_NORMAL = 0.6

    def __init__(self, agents: List[BaseAgent] = None):
        """
        Initialize the signal generator.

        Args:
            agents: List of agents to use for signal generation
        """
        self.agents: List[BaseAgent] = agents or []
        self.logger = logging.getLogger("signal_generator")

    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent for signal generation.

        Args:
            agent: Agent to register
        """
        if agent not in self.agents:
            self.agents.append(agent)
            self.logger.info(f"Registered agent: {agent.name}")

    def unregister_agent(self, agent_name: str) -> bool:
        """
        Unregister an agent by name.

        Args:
            agent_name: Name of the agent to remove

        Returns:
            True if agent was found and removed
        """
        for agent in self.agents:
            if agent.name == agent_name:
                self.agents.remove(agent)
                self.logger.info(f"Unregistered agent: {agent_name}")
                return True
        return False

    def generate_signal(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> ConsensusSignal:
        """
        Generate a consensus signal from all registered agents.

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data
            sentiment_data: Optional sentiment analysis data
            historical_data: Optional historical price data

        Returns:
            ConsensusSignal with aggregated recommendation
        """
        if not self.agents:
            return self._create_neutral_consensus(
                ticker, "No agents registered for signal generation"
            )

        if not ticker or not market_data:
            return self._create_neutral_consensus(
                ticker or "UNKNOWN", "Invalid input data"
            )

        # Collect signals from all agents
        agent_signals = self._collect_agent_signals(
            ticker, market_data, sentiment_data, historical_data
        )

        if not agent_signals:
            return self._create_neutral_consensus(
                ticker, "No valid signals from agents"
            )

        # Calculate weighted consensus
        weighted_score, total_weight = self._calculate_weighted_score(agent_signals)

        # Calculate agreement ratio
        agreement_ratio = self._calculate_agreement(agent_signals)

        # Calculate overall confidence
        confidence = self._calculate_consensus_confidence(
            agent_signals, agreement_ratio
        )

        # Determine signal type from score
        signal_type = self._score_to_signal(weighted_score)

        # Determine position size
        position_size = self._calculate_position_size(
            confidence, agreement_ratio, abs(weighted_score)
        )

        # Generate reasoning summary
        reasoning = self._generate_reasoning(
            agent_signals, signal_type, agreement_ratio
        )

        return ConsensusSignal(
            ticker=ticker,
            signal=signal_type,
            confidence=confidence,
            raw_score=weighted_score,
            position_size=position_size,
            agent_signals=agent_signals,
            agreement_ratio=agreement_ratio,
            reasoning=reasoning,
        )

    def _collect_agent_signals(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict],
        historical_data: Optional[List[Dict]],
    ) -> List[AgentSignal]:
        """Collect signals from all registered agents."""
        signals = []

        for agent in self.agents:
            try:
                signal = agent.analyze(
                    ticker=ticker,
                    market_data=market_data,
                    sentiment_data=sentiment_data,
                    historical_data=historical_data,
                )
                signals.append(signal)
                self.logger.debug(
                    f"Agent {agent.name}: {signal.signal.value} "
                    f"(score={signal.raw_score:.2f}, conf={signal.confidence:.2f})"
                )
            except Exception as e:
                self.logger.error(f"Agent {agent.name} failed: {e}")
                continue

        return signals

    def _calculate_weighted_score(
        self, signals: List[AgentSignal]
    ) -> Tuple[float, float]:
        """
        Calculate weighted average score from agent signals.

        Weight = agent_weight * signal_confidence

        Returns:
            Tuple of (weighted_score, total_weight)
        """
        total_weighted_score = 0.0
        total_weight = 0.0

        for signal in signals:
            # Find the agent weight
            agent_weight = 1.0
            for agent in self.agents:
                if agent.name == signal.agent_name:
                    agent_weight = agent.weight
                    break

            # Combined weight = agent importance * signal confidence
            combined_weight = agent_weight * (0.5 + signal.confidence * 0.5)

            total_weighted_score += signal.raw_score * combined_weight
            total_weight += combined_weight

        if total_weight == 0:
            return 0.0, 0.0

        return total_weighted_score / total_weight, total_weight

    def _calculate_agreement(self, signals: List[AgentSignal]) -> float:
        """
        Calculate how much agents agree on direction.

        Returns:
            Agreement ratio (0.0 to 1.0)
        """
        if len(signals) <= 1:
            return 1.0

        # Count bullish, bearish, and neutral signals
        bullish = sum(1 for s in signals if s.raw_score > 0.1)
        bearish = sum(1 for s in signals if s.raw_score < -0.1)
        neutral = len(signals) - bullish - bearish

        # Agreement is the proportion of the dominant direction
        max_direction = max(bullish, bearish, neutral)
        agreement = max_direction / len(signals)

        return agreement

    def _calculate_consensus_confidence(
        self, signals: List[AgentSignal], agreement_ratio: float
    ) -> float:
        """
        Calculate overall consensus confidence.

        Factors:
        - Average agent confidence
        - Agreement among agents
        - Number of agents (more agents = more reliable)
        """
        if not signals:
            return 0.0

        # Average confidence from agents
        avg_confidence = sum(s.confidence for s in signals) / len(signals)

        # Agent count factor (diminishing returns after 3 agents)
        agent_count_factor = min(len(signals) / 3, 1.0)

        # Combine factors
        # 50% from average confidence
        # 30% from agreement
        # 20% from agent count
        consensus_confidence = (
            avg_confidence * 0.5 + agreement_ratio * 0.3 + agent_count_factor * 0.2
        )

        return min(consensus_confidence, 1.0)

    def _score_to_signal(self, score: float) -> SignalType:
        """
        Convert numeric score to signal type.

        Thresholds adjusted for 14-day paper trading validation:
        - More sensitive to generate actionable BUY/SELL signals
        - Neutral zone reduced from ±0.2 to ±0.1
        """
        if score >= 0.5:
            return SignalType.STRONG_BUY
        elif score >= 0.1:
            return SignalType.BUY
        elif score >= -0.1:
            return SignalType.HOLD
        elif score >= -0.5:
            return SignalType.SELL
        else:
            return SignalType.STRONG_SELL

    def _calculate_position_size(
        self,
        confidence: float,
        agreement_ratio: float,
        score_strength: float,
    ) -> PositionSize:
        """
        Calculate recommended position size.

        Position size depends on:
        - Confidence level
        - Agreement among agents
        - Strength of the signal
        """
        # No position for weak signals or low confidence
        if score_strength < 0.1 or confidence < self.LOW_CONFIDENCE_THRESHOLD:
            return PositionSize.NONE

        # Large position: high confidence + high agreement + strong signal
        if (
            confidence >= self.HIGH_CONFIDENCE_THRESHOLD
            and agreement_ratio >= self.MIN_AGREEMENT_FOR_LARGE
            and score_strength >= 0.5
        ):
            return PositionSize.LARGE

        # Normal position: good confidence + good agreement
        if (
            confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD
            and agreement_ratio >= self.MIN_AGREEMENT_FOR_NORMAL
        ):
            return PositionSize.NORMAL

        # Medium position: moderate confidence
        if confidence >= self.LOW_CONFIDENCE_THRESHOLD:
            return PositionSize.MEDIUM

        # Small position: low confidence but actionable signal
        return PositionSize.SMALL

    def _generate_reasoning(
        self,
        signals: List[AgentSignal],
        final_signal: SignalType,
        agreement_ratio: float,
    ) -> str:
        """Generate human-readable reasoning summary."""
        if not signals:
            return "No agent signals available"

        # Count by direction
        bullish = [s for s in signals if s.raw_score > 0.1]
        bearish = [s for s in signals if s.raw_score < -0.1]

        # Build summary
        parts = []

        # Agreement summary
        if agreement_ratio >= 0.8:
            parts.append(f"Strong consensus ({agreement_ratio:.0%} agreement)")
        elif agreement_ratio >= 0.6:
            parts.append(f"Moderate consensus ({agreement_ratio:.0%} agreement)")
        else:
            parts.append(f"Mixed signals ({agreement_ratio:.0%} agreement)")

        # Direction summary
        if bullish:
            parts.append(f"{len(bullish)} bullish")
        if bearish:
            parts.append(f"{len(bearish)} bearish")

        # Top reasoning from highest confidence signal
        top_signal = max(signals, key=lambda s: s.confidence)
        if top_signal.reasoning:
            parts.append(f"Key: {top_signal.reasoning[:100]}")

        return "; ".join(parts)

    def _create_neutral_consensus(self, ticker: str, reason: str) -> ConsensusSignal:
        """Create a neutral consensus when analysis cannot be performed."""
        return ConsensusSignal(
            ticker=ticker,
            signal=SignalType.HOLD,
            confidence=0.0,
            raw_score=0.0,
            position_size=PositionSize.NONE,
            agent_signals=[],
            agreement_ratio=0.0,
            reasoning=reason,
        )

    def get_agent_names(self) -> List[str]:
        """Get names of all registered agents."""
        return [agent.name for agent in self.agents]

    def __repr__(self) -> str:
        agent_names = ", ".join(self.get_agent_names())
        return f"SignalGenerator(agents=[{agent_names}])"
