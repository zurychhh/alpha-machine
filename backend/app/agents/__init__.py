"""
AI Agents Module
Multi-agent system for stock analysis and signal generation

4-Agent System:
1. ContrarianAgent - GPT-4o powered deep value / contrarian analysis
2. GrowthAgent - Claude Sonnet 4 powered growth / momentum analysis
3. MultiModalAgent - Gemini Flash powered multi-modal synthesis
4. PredictorAgent - Rule-based technical predictor (MVP for LSTM)
"""

from app.agents.base_agent import BaseAgent, AgentSignal, SignalType
from app.agents.rule_based_agent import RuleBasedAgent
from app.agents.signal_generator import SignalGenerator, ConsensusSignal, PositionSize
from app.agents.contrarian_agent import ContrarianAgent
from app.agents.growth_agent import GrowthAgent
from app.agents.multimodal_agent import MultiModalAgent
from app.agents.predictor_agent import PredictorAgent

# Legacy imports for backwards compatibility
from app.agents.claude_agent import ClaudeAgent
from app.agents.gemini_agent import GeminiAgent

__all__ = [
    # Core
    "BaseAgent",
    "AgentSignal",
    "SignalType",
    # Signal Generation
    "SignalGenerator",
    "ConsensusSignal",
    "PositionSize",
    # 4-Agent System (BUILD_SPEC.md)
    "ContrarianAgent",  # GPT-4o
    "GrowthAgent",  # Claude Sonnet 4
    "MultiModalAgent",  # Gemini Flash
    "PredictorAgent",  # Rule-based MVP
    # Utility Agents
    "RuleBasedAgent",
    # Legacy (backwards compatibility)
    "ClaudeAgent",
    "GeminiAgent",
]
