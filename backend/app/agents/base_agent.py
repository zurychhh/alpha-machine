"""
Base Agent Abstract Class
Foundation for all AI agents in the multi-agent system
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trading signal types"""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class AgentSignal:
    """
    Standardized signal output from an agent.

    Attributes:
        agent_name: Name of the agent that generated the signal
        ticker: Stock ticker symbol
        signal: Trading signal type
        confidence: Confidence level (0.0 to 1.0)
        reasoning: Explanation of the signal
        factors: Key factors that influenced the decision
        timestamp: When the signal was generated
        raw_score: Underlying numeric score (-1.0 to 1.0)
    """

    agent_name: str
    ticker: str
    signal: SignalType
    confidence: float
    reasoning: str
    factors: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    raw_score: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "agent_name": self.agent_name,
            "ticker": self.ticker,
            "signal": self.signal.value,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "factors": self.factors,
            "timestamp": self.timestamp.isoformat(),
            "raw_score": round(self.raw_score, 3),
        }

    @classmethod
    def from_score(
        cls,
        agent_name: str,
        ticker: str,
        score: float,
        confidence: float,
        reasoning: str,
        factors: Dict[str, float] = None,
    ) -> "AgentSignal":
        """
        Create an AgentSignal from a numeric score.

        Args:
            agent_name: Name of the agent
            ticker: Stock ticker
            score: Numeric score from -1.0 (strong sell) to 1.0 (strong buy)
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Explanation of the signal
            factors: Contributing factors

        Returns:
            AgentSignal instance
        """
        # Clamp score to valid range
        score = max(-1.0, min(1.0, score))

        # Convert score to signal type
        if score >= 0.6:
            signal = SignalType.STRONG_BUY
        elif score >= 0.2:
            signal = SignalType.BUY
        elif score >= -0.2:
            signal = SignalType.HOLD
        elif score >= -0.6:
            signal = SignalType.SELL
        else:
            signal = SignalType.STRONG_SELL

        return cls(
            agent_name=agent_name,
            ticker=ticker,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            factors=factors or {},
            raw_score=score,
        )


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.

    Each agent represents a different analysis perspective:
    - Technical analysis
    - Fundamental analysis
    - Sentiment analysis
    - Contrarian view
    - Growth focus
    - etc.

    Agents should be stateless - they analyze data and produce signals
    without maintaining internal state between calls.
    """

    def __init__(self, name: str, weight: float = 1.0):
        """
        Initialize the agent.

        Args:
            name: Unique name for this agent
            weight: Weight of this agent's signal in consensus (default 1.0)
        """
        self.name = name
        self.weight = weight
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def analyze(
        self,
        ticker: str,
        market_data: Dict,
        sentiment_data: Optional[Dict] = None,
        historical_data: Optional[List[Dict]] = None,
    ) -> AgentSignal:
        """
        Analyze the data and produce a trading signal.

        This is the main method that each agent must implement.
        It should:
        1. Process the provided data according to its analysis strategy
        2. Calculate a score and confidence level
        3. Generate reasoning explaining the signal
        4. Return a standardized AgentSignal

        Args:
            ticker: Stock ticker symbol
            market_data: Current market data (price, volume, etc.)
            sentiment_data: Optional sentiment analysis data
            historical_data: Optional historical price data

        Returns:
            AgentSignal with the agent's recommendation
        """
        pass

    def validate_inputs(
        self,
        ticker: str,
        market_data: Dict,
    ) -> bool:
        """
        Validate that required inputs are present.

        Args:
            ticker: Stock ticker
            market_data: Market data dictionary

        Returns:
            True if inputs are valid
        """
        if not ticker or not isinstance(ticker, str):
            self.logger.warning("Invalid ticker provided")
            return False

        if not market_data or not isinstance(market_data, dict):
            self.logger.warning("Invalid market data provided")
            return False

        return True

    def create_neutral_signal(
        self,
        ticker: str,
        reason: str = "Insufficient data for analysis",
    ) -> AgentSignal:
        """
        Create a neutral HOLD signal when analysis cannot be performed.

        Args:
            ticker: Stock ticker
            reason: Explanation for the neutral signal

        Returns:
            AgentSignal with HOLD recommendation
        """
        return AgentSignal(
            agent_name=self.name,
            ticker=ticker,
            signal=SignalType.HOLD,
            confidence=0.0,
            reasoning=reason,
            factors={},
            raw_score=0.0,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', weight={self.weight})"
