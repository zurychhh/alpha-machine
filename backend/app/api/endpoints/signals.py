"""
Signals API Endpoints
Generate AI-powered trading signals using multi-agent consensus

4-Agent System (BUILD_SPEC.md):
1. ContrarianAgent - GPT-4o powered contrarian/deep value analysis
2. GrowthAgent - Claude Sonnet 4 powered growth/momentum analysis
3. MultiModalAgent - Gemini Flash powered multi-modal synthesis
4. PredictorAgent - Rule-based technical predictor (LSTM MVP)

Milestone 4 Features:
- Signal persistence to PostgreSQL
- Risk parameters (stop loss, target price)
- Signal history and details endpoints
- Batch signal generation for watchlist
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from sqlalchemy.orm import Session
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
from app.services.signal_service import get_signal_service
from app.core.config import settings
from app.core.database import get_db
from app.models.watchlist import Watchlist

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
    save: bool = Query(default=True, description="Save signal to database"),
    include_sentiment: bool = Query(default=True, description="Include sentiment data"),
    include_historical: bool = Query(
        default=True, description="Include historical data"
    ),
    days: int = Query(default=30, ge=1, le=90, description="Days of historical data"),
    portfolio_value: float = Query(
        default=100000.0, ge=1000, description="Portfolio value for position sizing"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate AI trading signal for a ticker

    Uses multi-agent consensus algorithm:
    - ContrarianAgent: GPT-4o contrarian analysis
    - GrowthAgent: Claude growth/momentum focus
    - MultiModalAgent: Gemini multi-modal synthesis
    - PredictorAgent: Rule-based technical patterns

    Returns:
    - Consensus signal (STRONG_BUY to STRONG_SELL)
    - Confidence score (0-1)
    - Position size recommendation
    - Risk parameters (stop_loss, target_price)
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

    entry_price = market_data.get("current_price")

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

    # Prepare response
    response = consensus.to_dict()

    # Save to database if requested
    if save:
        try:
            signal_service = get_signal_service(db)
            saved_signal = signal_service.save_signal(
                consensus=consensus,
                entry_price=entry_price,
                portfolio_value=portfolio_value,
            )
            response["saved"] = True
            response["signal_id"] = saved_signal.id
            response["entry_price"] = float(saved_signal.entry_price)
            response["stop_loss"] = float(saved_signal.stop_loss)
            response["target_price"] = float(saved_signal.target_price)
            response["shares"] = saved_signal.position_size
        except Exception as e:
            logger.error(f"Failed to save signal: {e}")
            response["saved"] = False
            response["save_error"] = str(e)
    else:
        response["saved"] = False

    return response


@router.get("")
async def list_signals(
    ticker: Optional[str] = Query(default=None, description="Filter by ticker"),
    signal_type: Optional[str] = Query(
        default=None, description="Filter by type (BUY, SELL, HOLD)"
    ),
    status: Optional[str] = Query(
        default=None, description="Filter by status (PENDING, APPROVED, EXECUTED, CLOSED)"
    ),
    days: int = Query(default=30, ge=1, le=365, description="Days to look back"),
    limit: int = Query(default=50, ge=1, le=200, description="Max signals to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    Get signal history with optional filtering

    Returns list of saved signals with:
    - Signal details (ticker, type, confidence)
    - Risk parameters (entry, stop_loss, target)
    - Status and P&L if closed
    """
    signal_service = get_signal_service(db)
    signals = signal_service.get_signals(
        ticker=ticker,
        signal_type=signal_type,
        status=status,
        days=days,
        limit=limit,
        offset=offset,
    )

    return {
        "count": len(signals),
        "signals": [signal_service.signal_to_dict(s) for s in signals],
    }


@router.get("/stats")
async def get_signal_statistics(
    days: int = Query(default=30, ge=1, le=365, description="Days to analyze"),
    db: Session = Depends(get_db),
):
    """
    Get signal statistics for the specified period

    Returns:
    - Total signals generated
    - Breakdown by type and status
    - Win rate for closed signals
    - Average P&L
    """
    signal_service = get_signal_service(db)
    return signal_service.get_statistics(days=days)


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


@router.get("/{signal_id}")
async def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
):
    """
    Get signal details by ID

    Returns full signal with:
    - All risk parameters
    - Individual agent analyses with reasoning
    - Execution status and P&L
    """
    signal_service = get_signal_service(db)
    signal = signal_service.get_signal(signal_id)

    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    return signal_service.signal_to_dict(signal)


@router.patch("/{signal_id}/status")
async def update_signal_status(
    signal_id: int,
    status: str = Query(..., description="New status"),
    pnl: Optional[float] = Query(default=None, description="P&L if closing"),
    notes: Optional[str] = Query(default=None, description="Notes"),
    db: Session = Depends(get_db),
):
    """
    Update signal status

    Valid status values:
    - PENDING: Awaiting approval
    - APPROVED: Ready for execution
    - EXECUTED: Trade placed
    - CLOSED: Position closed (include pnl)
    """
    valid_statuses = ["PENDING", "APPROVED", "EXECUTED", "CLOSED"]
    if status.upper() not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}",
        )

    signal_service = get_signal_service(db)
    updated = signal_service.update_signal_status(
        signal_id=signal_id,
        status=status,
        pnl=pnl,
        notes=notes,
    )

    if not updated:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")

    return signal_service.signal_to_dict(updated)


@router.post("/generate-all")
async def generate_all_signals(
    save: bool = Query(default=True, description="Save signals to database"),
    portfolio_value: float = Query(
        default=100000.0, ge=1000, description="Portfolio value for position sizing"
    ),
    db: Session = Depends(get_db),
):
    """
    Generate signals for all tickers in watchlist

    Useful for:
    - Daily signal generation
    - Batch analysis
    - Scheduled tasks

    Returns summary of all generated signals
    """
    # Get all tickers from watchlist
    watchlist = db.query(Watchlist).filter(Watchlist.is_active == True).all()

    if not watchlist:
        return {"message": "No active tickers in watchlist", "signals": []}

    generator = get_signal_generator()
    signal_service = get_signal_service(db)
    results = []

    for item in watchlist:
        ticker = item.ticker
        try:
            # Get market data
            market_data = market_data_service.get_quote(ticker)
            if market_data.get("current_price") is None:
                results.append({
                    "ticker": ticker,
                    "status": "error",
                    "error": "Could not fetch market data",
                })
                continue

            entry_price = market_data.get("current_price")

            # Add technical indicators
            technical = market_data_service.get_technical_indicators(ticker)
            market_data["indicators"] = technical

            # Get sentiment (optional, don't fail if unavailable)
            sentiment_data = None
            try:
                sentiment_data = sentiment_service.aggregate_sentiment(ticker)
            except Exception:
                pass

            # Generate signal
            consensus = generator.generate_signal(
                ticker=ticker,
                market_data=market_data,
                sentiment_data=sentiment_data,
            )

            result = {
                "ticker": ticker,
                "signal": consensus.signal.value,
                "confidence": round(consensus.confidence, 3),
                "status": "success",
            }

            # Save to database if requested
            if save:
                try:
                    saved_signal = signal_service.save_signal(
                        consensus=consensus,
                        entry_price=entry_price,
                        portfolio_value=portfolio_value,
                    )
                    result["signal_id"] = saved_signal.id
                    result["saved"] = True
                except Exception as e:
                    result["saved"] = False
                    result["save_error"] = str(e)

            results.append(result)

        except Exception as e:
            logger.error(f"Failed to generate signal for {ticker}: {e}")
            results.append({
                "ticker": ticker,
                "status": "error",
                "error": str(e),
            })

    # Summary
    successful = [r for r in results if r.get("status") == "success"]
    buy_signals = [r for r in successful if "BUY" in r.get("signal", "")]
    sell_signals = [r for r in successful if "SELL" in r.get("signal", "")]

    return {
        "total": len(watchlist),
        "successful": len(successful),
        "failed": len(results) - len(successful),
        "buy_signals": len(buy_signals),
        "sell_signals": len(sell_signals),
        "signals": results,
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
