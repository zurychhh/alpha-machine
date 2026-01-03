"""
Signals API Endpoints
Generate AI-powered trading signals using multi-agent consensus

4-Agent System (BUILD_SPEC.md):
1. ContrarianAgent - GPT-4o powered contrarian/deep value analysis
2. GrowthAgent - Claude Sonnet 4 powered growth/momentum analysis
3. MultiModalAgent - Gemini Flash powered multi-modal synthesis
4. PredictorAgent - Rule-based technical predictor (LSTM MVP)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging

from app.agents import (
    SignalGenerator,
    ContrarianAgent,
    GrowthAgent,
    MultiModalAgent,
    PredictorAgent,
)
from app.services.market_data import market_data_service
from app.services.sentiment_data import sentiment_service
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize agents - lazy initialization for API key validation
_signal_generator: Optional[SignalGenerator] = None


def get_signal_generator() -> SignalGenerator:
    """
    Get or create the signal generator with all 4 agents.

    4-Agent System:
    1. ContrarianAgent (GPT-4o) - Contrarian/deep value analysis
    2. GrowthAgent (Claude) - Growth/momentum analysis
    3. MultiModalAgent (Gemini) - Multi-modal synthesis
    4. PredictorAgent (Rule-based) - Technical predictor

    Uses lazy initialization to avoid startup errors if API keys are missing.
    """
    global _signal_generator

    if _signal_generator is None:
        agents = []

        # Agent 1: Contrarian (GPT-4o)
        try:
            api_key = settings.OPENAI_API_KEY
            if api_key:
                contrarian = ContrarianAgent(
                    name="ContrarianAgent", weight=1.0, api_key=api_key
                )
                agents.append(contrarian)
                logger.info("ContrarianAgent (GPT-4o) initialized")
            else:
                logger.warning("ContrarianAgent skipped - no OpenAI API key")
        except Exception as e:
            logger.warning(f"ContrarianAgent initialization failed: {e}")

        # Agent 2: Growth (Claude Sonnet 4)
        try:
            api_key = settings.ANTHROPIC_API_KEY
            if api_key:
                growth = GrowthAgent(
                    name="GrowthAgent", weight=1.0, api_key=api_key
                )
                agents.append(growth)
                logger.info("GrowthAgent (Claude) initialized")
            else:
                logger.warning("GrowthAgent skipped - no Anthropic API key")
        except Exception as e:
            logger.warning(f"GrowthAgent initialization failed: {e}")

        # Agent 3: MultiModal (Gemini Flash)
        try:
            api_key = settings.GOOGLE_AI_API_KEY
            if api_key:
                multimodal = MultiModalAgent(
                    name="MultiModalAgent", weight=1.0, api_key=api_key
                )
                agents.append(multimodal)
                logger.info("MultiModalAgent (Gemini) initialized")
            else:
                logger.warning("MultiModalAgent skipped - no Google AI API key")
        except Exception as e:
            logger.warning(f"MultiModalAgent initialization failed: {e}")

        # Agent 4: Predictor (Rule-based MVP)
        predictor = PredictorAgent(name="PredictorAgent", weight=1.0)
        agents.append(predictor)
        logger.info("PredictorAgent (Rule-based) initialized")

        _signal_generator = SignalGenerator(agents=agents)
        logger.info(f"Signal generator initialized with {len(agents)} agents")

    return _signal_generator


@router.post("/generate/{ticker}")
async def generate_signal(
    ticker: str,
    include_sentiment: bool = Query(default=True, description="Include sentiment data"),
    include_historical: bool = Query(
        default=True, description="Include historical data"
    ),
    days: int = Query(default=30, ge=1, le=90, description="Days of historical data"),
):
    """
    Generate AI trading signal for a ticker

    Uses multi-agent consensus algorithm:
    - Claude Agent: Contrarian analysis
    - Gemini Agent: Growth focus
    - Predictor Agent: Technical patterns
    - Rule-Based Agent: Baseline signals

    Returns:
    - Consensus signal (STRONG_BUY to STRONG_SELL)
    - Confidence score (0-1)
    - Position size recommendation
    - Individual agent signals
    - Reasoning breakdown
    """
    ticker = ticker.upper()

    # Validate ticker format
    if not ticker.isalpha() or len(ticker) > 5:
        raise HTTPException(status_code=400, detail="Invalid ticker format")

    # Get market data
    market_data = market_data_service.get_quote(ticker)
    if market_data.get("current_price") is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch market data for {ticker}",
        )

    # Add technical indicators
    technical = market_data_service.get_technical_indicators(ticker)
    market_data["indicators"] = technical

    # Get sentiment data if requested
    sentiment_data = None
    if include_sentiment:
        try:
            sentiment_data = sentiment_service.aggregate_sentiment(ticker)
        except Exception as e:
            logger.warning(f"Failed to get sentiment for {ticker}: {e}")

    # Get historical data if requested
    historical_data = None
    if include_historical:
        try:
            historical_data = market_data_service.get_historical_data(ticker, days=days)
        except Exception as e:
            logger.warning(f"Failed to get historical data for {ticker}: {e}")

    # Generate signal using all agents
    generator = get_signal_generator()
    consensus = generator.generate_signal(
        ticker=ticker,
        market_data=market_data,
        sentiment_data=sentiment_data,
        historical_data=historical_data,
    )

    return consensus.to_dict()


@router.get("/agents")
async def list_agents():
    """
    List all registered agents and their status

    Returns:
    - Agent names and weights
    - Agent types
    - API status (connected/unavailable)
    - Model being used
    """
    generator = get_signal_generator()

    agents_info = []
    for agent in generator.agents:
        info = {
            "name": agent.name,
            "weight": agent.weight,
            "type": agent.__class__.__name__,
        }

        # Check API availability and add model info for AI agents
        if isinstance(agent, ContrarianAgent):
            info["api_status"] = "connected" if agent.api_key else "no_api_key"
            info["model"] = agent.model_name
            info["provider"] = "OpenAI"
        elif isinstance(agent, GrowthAgent):
            info["api_status"] = "connected" if agent.api_key else "no_api_key"
            info["model"] = agent.model_name
            info["provider"] = "Anthropic"
        elif isinstance(agent, MultiModalAgent):
            info["api_status"] = "connected" if agent.api_key else "no_api_key"
            info["model"] = agent.model_name
            info["provider"] = "Google"
        elif isinstance(agent, PredictorAgent):
            info["api_status"] = "not_required"
            info["model"] = "rule-based"
            info["provider"] = "local"
        else:
            info["api_status"] = "not_required"

        agents_info.append(info)

    return {
        "agent_count": len(agents_info),
        "agents": agents_info,
    }


@router.post("/analyze/{ticker}/single")
async def analyze_single_agent(
    ticker: str,
    agent_name: str = Query(..., description="Name of the agent to use"),
):
    """
    Get analysis from a single agent (for debugging/comparison)

    Returns the raw signal from the specified agent
    """
    ticker = ticker.upper()
    generator = get_signal_generator()

    # Find the agent
    agent = None
    for a in generator.agents:
        if a.name.lower() == agent_name.lower():
            agent = a
            break

    if agent is None:
        available = [a.name for a in generator.agents]
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found. Available: {available}",
        )

    # Get market data
    market_data = market_data_service.get_quote(ticker)
    if market_data.get("current_price") is None:
        raise HTTPException(
            status_code=404, detail=f"Could not fetch data for {ticker}"
        )

    technical = market_data_service.get_technical_indicators(ticker)
    market_data["indicators"] = technical

    # Get sentiment data
    try:
        sentiment_data = sentiment_service.aggregate_sentiment(ticker)
    except Exception:
        sentiment_data = None

    # Get analysis from single agent
    try:
        signal = agent.analyze(
            ticker=ticker,
            market_data=market_data,
            sentiment_data=sentiment_data,
        )
        return signal.to_dict()
    except Exception as e:
        logger.error(f"Agent {agent_name} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent analysis failed: {str(e)}")


@router.get("/test/{ticker}")
async def test_signal_generation(ticker: str):
    """
    Quick test endpoint for signal generation

    Returns simplified signal without all agent details
    """
    ticker = ticker.upper()

    # Get basic market data
    market_data = market_data_service.get_quote(ticker)
    if market_data.get("current_price") is None:
        raise HTTPException(
            status_code=404, detail=f"Could not fetch data for {ticker}"
        )

    technical = market_data_service.get_technical_indicators(ticker)
    market_data["indicators"] = technical

    generator = get_signal_generator()
    consensus = generator.generate_signal(
        ticker=ticker,
        market_data=market_data,
    )

    return {
        "ticker": ticker,
        "signal": consensus.signal.value,
        "confidence": round(consensus.confidence, 2),
        "position_size": consensus.position_size.value,
        "raw_score": round(consensus.raw_score, 3),
        "agents_used": len(consensus.agent_signals),
        "reasoning": consensus.reasoning[:200],
    }
