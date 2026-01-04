"""
Signal Tasks - Scheduled signal generation for Alpha Machine

Tasks:
- generate_daily_signals_task: Generate signals for all watchlist stocks
- generate_signal_for_ticker: Generate signal for a single ticker
- analyze_signal_performance_task: Analyze performance of past signals
"""

from celery import shared_task
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.watchlist import Watchlist
from app.models.signal import Signal
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

logger = logging.getLogger(__name__)


def get_signal_generator() -> SignalGenerator:
    """
    Create and configure the signal generator with all 4 agents.

    Returns:
        Configured SignalGenerator instance
    """
    agents = []

    # Agent 1: Contrarian (GPT-4o)
    if settings.OPENAI_API_KEY:
        try:
            agents.append(ContrarianAgent(
                name="ContrarianAgent",
                weight=1.0,
                api_key=settings.OPENAI_API_KEY,
            ))
        except Exception as e:
            logger.warning(f"ContrarianAgent init failed: {e}")

    # Agent 2: Growth (Claude)
    if settings.ANTHROPIC_API_KEY:
        try:
            agents.append(GrowthAgent(
                name="GrowthAgent",
                weight=1.0,
                api_key=settings.ANTHROPIC_API_KEY,
            ))
        except Exception as e:
            logger.warning(f"GrowthAgent init failed: {e}")

    # Agent 3: MultiModal (Gemini)
    if settings.GOOGLE_AI_API_KEY:
        try:
            agents.append(MultiModalAgent(
                name="MultiModalAgent",
                weight=1.0,
                api_key=settings.GOOGLE_AI_API_KEY,
            ))
        except Exception as e:
            logger.warning(f"MultiModalAgent init failed: {e}")

    # Agent 4: Predictor (Rule-based - always available)
    agents.append(PredictorAgent(name="PredictorAgent", weight=1.0))

    return SignalGenerator(agents=agents)


@shared_task(
    bind=True,
    name="app.tasks.signal_tasks.generate_daily_signals_task",
    max_retries=2,
    default_retry_delay=300,
)
def generate_daily_signals_task(
    self,
    portfolio_value: float = 100000.0,
) -> Dict[str, Any]:
    """
    Generate trading signals for all active watchlist stocks.

    Runs daily at 9:00 AM EST (before market open) and 12:00 PM EST.
    Saves all signals to the database.

    Args:
        portfolio_value: Portfolio value for position sizing

    Returns:
        Dict with generation results and statistics
    """
    db = SessionLocal()
    results = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "successful": 0,
        "failed": 0,
        "buy_signals": 0,
        "sell_signals": 0,
        "hold_signals": 0,
        "signals": [],
    }

    try:
        # Get all active tickers from watchlist
        watchlist = db.query(Watchlist).filter(Watchlist.active == True).all()

        if not watchlist:
            results["status"] = "no_tickers"
            return results

        generator = get_signal_generator()
        signal_service = get_signal_service(db)

        logger.info(
            f"Starting daily signal generation for {len(watchlist)} tickers "
            f"with {len(generator.agents)} agents"
        )

        for item in watchlist:
            ticker = item.ticker
            try:
                # Fetch market data
                market_data = market_data_service.get_quote(ticker)
                if market_data.get("current_price") is None:
                    results["failed"] += 1
                    results["signals"].append({
                        "ticker": ticker,
                        "status": "error",
                        "error": "No market data",
                    })
                    continue

                entry_price = market_data.get("current_price")

                # Add technical indicators
                technical = market_data_service.get_technical_indicators(ticker)
                market_data["indicators"] = technical

                # Fetch sentiment (optional)
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

                # Save to database
                saved_signal = signal_service.save_signal(
                    consensus=consensus,
                    entry_price=entry_price,
                    portfolio_value=portfolio_value,
                )

                # Update counts
                signal_type = consensus.signal.value
                if "BUY" in signal_type:
                    results["buy_signals"] += 1
                elif "SELL" in signal_type:
                    results["sell_signals"] += 1
                else:
                    results["hold_signals"] += 1

                results["successful"] += 1
                results["signals"].append({
                    "ticker": ticker,
                    "signal_id": saved_signal.id,
                    "signal_type": saved_signal.signal_type,
                    "confidence": saved_signal.confidence,
                    "entry_price": float(saved_signal.entry_price),
                    "status": "success",
                })

                logger.info(
                    f"Generated signal for {ticker}: {saved_signal.signal_type} "
                    f"(confidence: {saved_signal.confidence})"
                )

            except Exception as e:
                logger.error(f"Signal generation failed for {ticker}: {e}")
                results["failed"] += 1
                results["signals"].append({
                    "ticker": ticker,
                    "status": "error",
                    "error": str(e),
                })

        results["status"] = "completed"
        results["total_processed"] = len(watchlist)

    except Exception as e:
        logger.error(f"Daily signal generation task failed: {e}")
        results["status"] = "error"
        results["error"] = str(e)
        raise self.retry(exc=e)

    finally:
        db.close()

    logger.info(
        f"Daily signal generation completed: {results['successful']} success, "
        f"{results['failed']} failed. BUY: {results['buy_signals']}, "
        f"SELL: {results['sell_signals']}, HOLD: {results['hold_signals']}"
    )

    return results


@shared_task(name="app.tasks.signal_tasks.generate_signal_for_ticker")
def generate_signal_for_ticker(
    ticker: str,
    portfolio_value: float = 100000.0,
    save: bool = True,
) -> Dict[str, Any]:
    """
    Generate signal for a single ticker.

    Can be called on-demand for specific stocks.

    Args:
        ticker: Stock ticker symbol
        portfolio_value: Portfolio value for position sizing
        save: Whether to save to database

    Returns:
        Dict with signal details
    """
    ticker = ticker.upper()
    db = SessionLocal() if save else None

    result = {
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
    }

    try:
        # Fetch market data
        market_data = market_data_service.get_quote(ticker)
        if market_data.get("current_price") is None:
            result["status"] = "error"
            result["error"] = "No market data available"
            return result

        entry_price = market_data.get("current_price")

        # Add technical indicators
        technical = market_data_service.get_technical_indicators(ticker)
        market_data["indicators"] = technical

        # Fetch sentiment
        sentiment_data = None
        try:
            sentiment_data = sentiment_service.aggregate_sentiment(ticker)
        except Exception:
            pass

        # Generate signal
        generator = get_signal_generator()
        consensus = generator.generate_signal(
            ticker=ticker,
            market_data=market_data,
            sentiment_data=sentiment_data,
        )

        result["signal"] = consensus.signal.value
        result["confidence"] = round(consensus.confidence, 3)
        result["raw_score"] = round(consensus.raw_score, 3)
        result["position_size"] = consensus.position_size.value
        result["reasoning"] = consensus.reasoning
        result["agents_used"] = len(consensus.agent_signals)

        # Save to database if requested
        if save and db:
            signal_service = get_signal_service(db)
            saved_signal = signal_service.save_signal(
                consensus=consensus,
                entry_price=entry_price,
                portfolio_value=portfolio_value,
            )
            result["signal_id"] = saved_signal.id
            result["entry_price"] = float(saved_signal.entry_price)
            result["stop_loss"] = float(saved_signal.stop_loss)
            result["target_price"] = float(saved_signal.target_price)
            result["saved"] = True

    except Exception as e:
        logger.error(f"Signal generation failed for {ticker}: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    finally:
        if db:
            db.close()

    return result


@shared_task(
    bind=True,
    name="app.tasks.signal_tasks.analyze_signal_performance_task",
    max_retries=1,
)
def analyze_signal_performance_task(self, days: int = 7) -> Dict[str, Any]:
    """
    Analyze performance of signals from the past N days.

    Runs daily at 4:30 PM EST (after market close).
    Compares signal predictions with actual price movements.

    Args:
        days: Number of days to analyze

    Returns:
        Dict with performance statistics
    """
    db = SessionLocal()
    results = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "period_days": days,
        "signals_analyzed": 0,
        "correct_predictions": 0,
        "accuracy": None,
        "details": [],
    }

    try:
        # Get signals from the past N days
        since = datetime.utcnow() - timedelta(days=days)
        signals = (
            db.query(Signal)
            .filter(Signal.timestamp >= since)
            .filter(Signal.status.in_(["PENDING", "APPROVED", "EXECUTED"]))
            .all()
        )

        if not signals:
            results["status"] = "no_signals"
            return results

        for signal in signals:
            try:
                # Get current price
                quote = market_data_service.get_quote(signal.ticker)
                current_price = quote.get("current_price")

                if current_price and signal.entry_price:
                    entry = float(signal.entry_price)
                    price_change = (current_price - entry) / entry * 100

                    # Check if prediction was correct
                    correct = False
                    if signal.signal_type == "BUY" and price_change > 0:
                        correct = True
                    elif signal.signal_type == "SELL" and price_change < 0:
                        correct = True
                    elif signal.signal_type == "HOLD" and abs(price_change) < 5:
                        correct = True

                    if correct:
                        results["correct_predictions"] += 1

                    results["signals_analyzed"] += 1
                    results["details"].append({
                        "signal_id": signal.id,
                        "ticker": signal.ticker,
                        "signal_type": signal.signal_type,
                        "entry_price": entry,
                        "current_price": current_price,
                        "price_change_percent": round(price_change, 2),
                        "correct": correct,
                    })

            except Exception as e:
                logger.warning(f"Could not analyze signal {signal.id}: {e}")

        # Calculate accuracy
        if results["signals_analyzed"] > 0:
            results["accuracy"] = round(
                results["correct_predictions"] / results["signals_analyzed"], 3
            )

        results["status"] = "completed"

    except Exception as e:
        logger.error(f"Performance analysis task failed: {e}")
        results["status"] = "error"
        results["error"] = str(e)

    finally:
        db.close()

    logger.info(
        f"Signal performance analysis: {results['signals_analyzed']} signals, "
        f"{results['accuracy']:.1%} accuracy" if results["accuracy"] else
        f"Signal performance analysis completed: {results['signals_analyzed']} signals"
    )

    return results


@shared_task(name="app.tasks.signal_tasks.generate_high_confidence_alerts")
def generate_high_confidence_alerts(
    min_confidence: int = 4,
    days: int = 1,
) -> Dict[str, Any]:
    """
    Find high-confidence signals for potential alerts.

    Can be used to send notifications for strong signals.

    Args:
        min_confidence: Minimum confidence level (1-5)
        days: Look back period

    Returns:
        Dict with high-confidence signals
    """
    db = SessionLocal()

    try:
        since = datetime.utcnow() - timedelta(days=days)
        signals = (
            db.query(Signal)
            .filter(Signal.timestamp >= since)
            .filter(Signal.confidence >= min_confidence)
            .filter(Signal.signal_type.in_(["BUY", "SELL"]))
            .filter(Signal.status == "PENDING")
            .order_by(Signal.confidence.desc())
            .all()
        )

        return {
            "status": "success",
            "count": len(signals),
            "min_confidence": min_confidence,
            "signals": [
                {
                    "id": s.id,
                    "ticker": s.ticker,
                    "signal_type": s.signal_type,
                    "confidence": s.confidence,
                    "entry_price": float(s.entry_price) if s.entry_price else None,
                    "target_price": float(s.target_price) if s.target_price else None,
                    "stop_loss": float(s.stop_loss) if s.stop_loss else None,
                }
                for s in signals
            ],
        }

    finally:
        db.close()
