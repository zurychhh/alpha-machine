"""
Backtest API Endpoints

Provides endpoints for:
- Running backtests
- Comparing allocation modes
- Retrieving backtest results
- Analyzing agent performance
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import date

from app.core.database import get_db
from app.services.backtesting import backtest_engine
from app.services.portfolio_allocator import AllocationMode, portfolio_allocator
from app.models.backtest_result import BacktestResult
from app.models.signal import Signal
from app.models.agent_analysis import AgentAnalysis

router = APIRouter()


# Request/Response Models
class BacktestRequest(BaseModel):
    """Request model for running a backtest."""

    start_date: str = Field(
        ...,
        description="Start date in YYYY-MM-DD format",
        examples=["2024-12-01"],
    )
    end_date: str = Field(
        ...,
        description="End date in YYYY-MM-DD format",
        examples=["2025-01-01"],
    )
    mode: AllocationMode = Field(
        ...,
        description="Portfolio allocation mode",
        examples=["CORE_FOCUS"],
    )
    starting_capital: float = Field(
        default=50000.0,
        description="Starting capital in dollars",
        ge=1000,
        le=10000000,
    )
    hold_period_days: int = Field(
        default=7,
        description="Days to hold each position",
        ge=1,
        le=90,
    )
    tickers: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific tickers to include",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-12-01",
                "end_date": "2025-01-01",
                "mode": "CORE_FOCUS",
                "starting_capital": 50000,
                "hold_period_days": 7,
            }
        }


class CapitalSummary(BaseModel):
    starting: float
    ending: float
    return_pct: float


class TradeSummary(BaseModel):
    total: int
    wins: int
    losses: int
    win_rate: float


class BacktestResponse(BaseModel):
    """Response model for backtest results."""

    backtest_id: str
    mode: str
    period: dict
    capital: dict
    trades: dict
    metrics: dict

    class Config:
        from_attributes = True


# Endpoints
@router.post("/run", response_model=BacktestResponse)
def run_backtest(request: BacktestRequest, db: Session = Depends(get_db)):
    """
    Run a backtest for a date range.

    Simulates portfolio performance using historical signals
    with the specified allocation strategy.

    Returns comprehensive metrics including P&L, win rate, Sharpe ratio, etc.
    """
    results = backtest_engine.run_backtest(
        db=db,
        start_date=request.start_date,
        end_date=request.end_date,
        mode=request.mode,
        starting_capital=request.starting_capital,
        hold_period_days=request.hold_period_days,
        tickers=request.tickers,
    )

    if "error" in results:
        raise HTTPException(status_code=404, detail=results["error"])

    return results


@router.get("/{backtest_id}/results")
def get_backtest_results(backtest_id: str, db: Session = Depends(get_db)):
    """
    Get all trade results for a specific backtest.

    Returns detailed list of individual trades with P&L information.
    """
    results = (
        db.query(BacktestResult)
        .filter(BacktestResult.backtest_id == backtest_id)
        .order_by(BacktestResult.entry_date)
        .all()
    )

    if not results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    trades = []
    for r in results:
        # Get ticker from associated signal
        signal = db.query(Signal).filter(Signal.id == r.signal_id).first()
        ticker = signal.ticker if signal else "UNKNOWN"

        trades.append(
            {
                "id": r.id,
                "signal_id": r.signal_id,
                "ticker": ticker,
                "entry_date": r.entry_date.isoformat() if r.entry_date else None,
                "exit_date": r.exit_date.isoformat() if r.exit_date else None,
                "entry_price": float(r.entry_price) if r.entry_price else None,
                "exit_price": float(r.exit_price) if r.exit_price else None,
                "shares": r.shares,
                "pnl": float(r.pnl) if r.pnl else 0.0,
                "pnl_pct": float(r.pnl_pct) if r.pnl_pct else 0.0,
                "trade_result": r.trade_result,
                "days_held": r.days_held,
                "exit_reason": r.exit_reason,
                "position_type": r.position_type,
                "allocation_pct": float(r.allocation_pct) if r.allocation_pct else None,
            }
        )

    return {"backtest_id": backtest_id, "trade_count": len(trades), "trades": trades}


@router.get("/{backtest_id}/agent-performance")
def get_agent_performance(backtest_id: str, db: Session = Depends(get_db)):
    """
    Get agent performance breakdown for a backtest.

    Shows which agents' signals performed best in terms of:
    - Win rate
    - Total P&L
    - Number of trades
    """
    results = (
        db.query(BacktestResult)
        .filter(BacktestResult.backtest_id == backtest_id)
        .all()
    )

    if not results:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Aggregate by agent
    agent_stats = {}

    for result in results:
        # Get agent analyses for this signal
        analyses = (
            db.query(AgentAnalysis)
            .filter(AgentAnalysis.signal_id == result.signal_id)
            .all()
        )

        for analysis in analyses:
            agent = analysis.agent_name

            if agent not in agent_stats:
                agent_stats[agent] = {
                    "agent_name": agent,
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "total_pnl": 0.0,
                    "avg_confidence": 0.0,
                    "confidence_sum": 0,
                }

            agent_stats[agent]["trades"] += 1

            if result.trade_result == "WIN":
                agent_stats[agent]["wins"] += 1
            else:
                agent_stats[agent]["losses"] += 1

            agent_stats[agent]["total_pnl"] += float(result.pnl)
            agent_stats[agent]["confidence_sum"] += analysis.confidence

    # Calculate derived metrics
    for agent, stats in agent_stats.items():
        if stats["trades"] > 0:
            stats["win_rate"] = round(stats["wins"] / stats["trades"], 3)
            stats["avg_confidence"] = round(stats["confidence_sum"] / stats["trades"], 2)
            stats["avg_pnl_per_trade"] = round(stats["total_pnl"] / stats["trades"], 2)
        else:
            stats["win_rate"] = 0.0
            stats["avg_pnl_per_trade"] = 0.0

        stats["total_pnl"] = round(stats["total_pnl"], 2)
        del stats["confidence_sum"]  # Remove intermediate value

    # Sort by total P&L descending
    sorted_agents = sorted(
        agent_stats.values(), key=lambda x: x["total_pnl"], reverse=True
    )

    return {"backtest_id": backtest_id, "agent_performance": sorted_agents}


@router.post("/compare-modes")
def compare_allocation_modes(request: BacktestRequest, db: Session = Depends(get_db)):
    """
    Run backtest with all 3 allocation modes and compare results.

    Returns side-by-side comparison of:
    - CORE_FOCUS
    - BALANCED
    - DIVERSIFIED

    Identifies which mode performed best based on Sharpe ratio.
    """
    modes: List[AllocationMode] = ["CORE_FOCUS", "BALANCED", "DIVERSIFIED"]
    results = {}

    for mode in modes:
        mode_results = backtest_engine.run_backtest(
            db=db,
            start_date=request.start_date,
            end_date=request.end_date,
            mode=mode,
            starting_capital=request.starting_capital,
            hold_period_days=request.hold_period_days,
            tickers=request.tickers,
        )

        if "error" not in mode_results:
            results[mode] = {
                "backtest_id": mode_results["backtest_id"],
                "total_return_pct": mode_results["capital"]["return_pct"],
                "total_pnl": mode_results["metrics"]["total_pnl"],
                "win_rate": mode_results["trades"]["win_rate"],
                "sharpe_ratio": mode_results["metrics"]["sharpe_ratio"],
                "max_drawdown": mode_results["metrics"]["max_drawdown"],
                "total_trades": mode_results["trades"]["total"],
                "profit_factor": mode_results["metrics"]["profit_factor"],
            }
        else:
            results[mode] = {"error": mode_results["error"]}

    # Determine winner by Sharpe ratio (or return if Sharpe is equal)
    valid_results = {k: v for k, v in results.items() if "error" not in v}
    if valid_results:
        winner = max(
            valid_results.items(),
            key=lambda x: (x[1]["sharpe_ratio"], x[1]["total_return_pct"]),
        )[0]
    else:
        winner = None

    return {
        "period": {"start": request.start_date, "end": request.end_date},
        "starting_capital": request.starting_capital,
        "comparison": results,
        "winner": winner,
        "winner_reason": "Highest Sharpe ratio" if winner else "No valid results",
    }


@router.get("/modes")
def get_allocation_modes():
    """
    Get descriptions of available allocation modes.

    Useful for UI to display mode options to users.
    """
    modes: List[AllocationMode] = ["CORE_FOCUS", "BALANCED", "DIVERSIFIED"]
    return {
        "modes": [
            {"mode": mode, **portfolio_allocator.get_mode_description(mode)}
            for mode in modes
        ]
    }


@router.get("/history")
def get_backtest_history(
    limit: int = 20, offset: int = 0, db: Session = Depends(get_db)
):
    """
    Get history of past backtest runs.

    Returns list of unique backtest IDs with summary info.
    """
    # Get unique backtest IDs with aggregate info
    from sqlalchemy import func, distinct

    subquery = (
        db.query(
            BacktestResult.backtest_id,
            func.count(BacktestResult.id).label("trade_count"),
            func.sum(BacktestResult.pnl).label("total_pnl"),
            func.min(BacktestResult.entry_date).label("start_date"),
            func.max(BacktestResult.exit_date).label("end_date"),
            func.max(BacktestResult.created_at).label("created_at"),
        )
        .group_by(BacktestResult.backtest_id)
        .order_by(func.max(BacktestResult.created_at).desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    history = []
    for row in subquery:
        history.append(
            {
                "backtest_id": row.backtest_id,
                "trade_count": row.trade_count,
                "total_pnl": float(row.total_pnl) if row.total_pnl else 0.0,
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )

    return {"count": len(history), "offset": offset, "limit": limit, "backtests": history}


@router.delete("/{backtest_id}")
def delete_backtest(backtest_id: str, db: Session = Depends(get_db)):
    """
    Delete a backtest and all its trade results.
    """
    count = (
        db.query(BacktestResult)
        .filter(BacktestResult.backtest_id == backtest_id)
        .delete()
    )

    if count == 0:
        raise HTTPException(status_code=404, detail="Backtest not found")

    db.commit()

    return {"message": f"Deleted backtest {backtest_id}", "trades_deleted": count}
