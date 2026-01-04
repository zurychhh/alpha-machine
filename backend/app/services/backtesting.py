"""
Backtest Engine - Simulates historical execution of trading strategy.

Main service for running backtests to validate signal quality and
compare allocation strategies.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.models.backtest_result import BacktestResult
from app.services.signal_ranker import signal_ranker
from app.services.portfolio_allocator import portfolio_allocator, AllocationMode
from app.services.market_data import market_data_service

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Main backtest simulation engine."""

    def run_backtest(
        self,
        db: Session,
        start_date: str,
        end_date: str,
        mode: AllocationMode,
        starting_capital: float = 50000.0,
        hold_period_days: int = 7,
        tickers: Optional[List[str]] = None,
    ) -> Dict:
        """
        Run a complete backtest simulation.

        Process:
        1. Fetch all signals from date range
        2. Group signals by day
        3. For each day: rank signals, allocate portfolio, simulate trades
        4. Calculate P&L and metrics
        5. Store results in database

        Args:
            db: Database session
            start_date: Backtest start (format: "2024-12-01")
            end_date: Backtest end (format: "2025-01-01")
            mode: Allocation strategy (CORE_FOCUS, BALANCED, DIVERSIFIED)
            starting_capital: Starting capital in dollars (default 50000)
            hold_period_days: Days to hold each position (default 7)
            tickers: Optional list of specific tickers to include

        Returns:
            Comprehensive backtest results dictionary:
            {
                "backtest_id": "uuid",
                "mode": "CORE_FOCUS",
                "period": {"start": "2024-12-01", "end": "2025-01-01"},
                "capital": {"starting": 50000, "ending": 62450, "return_pct": 24.9},
                "trades": {"total": 45, "wins": 31, "losses": 14, "win_rate": 0.688},
                "metrics": {"total_pnl": 12450.00, "sharpe_ratio": 1.85, ...},
                "backtest_result_ids": [1, 2, 3, ...]
            }
        """
        backtest_id = str(uuid.uuid4())

        logger.info(
            f"Starting backtest {backtest_id[:8]} | Mode: {mode} | "
            f"Period: {start_date} to {end_date} | Capital: ${starting_capital:,.2f}"
        )

        # Parse date strings to datetime for proper SQL comparison
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )

        # 1. Fetch signals from date range
        query = db.query(Signal).filter(
            Signal.timestamp >= start_dt,
            Signal.timestamp <= end_dt,
            Signal.signal_type == "BUY",
        )

        if tickers:
            query = query.filter(Signal.ticker.in_(tickers))

        signals = query.order_by(Signal.timestamp).all()

        logger.info(f"Found {len(signals)} BUY signals in backtest period")

        if len(signals) == 0:
            return {
                "backtest_id": backtest_id,
                "error": "No BUY signals found in date range",
                "period": {"start": start_date, "end": end_date},
            }

        # 2. Group signals by day
        signals_by_day = self._group_signals_by_day(signals)

        # 3. Simulate each trading day
        all_trades: List[BacktestResult] = []
        equity_curve = [{"date": start_date, "value": starting_capital}]

        for trade_date, day_signals in signals_by_day.items():
            # Rank signals for this day
            ranked = signal_ranker.rank_signals(day_signals, db)

            if not ranked:
                continue

            # Allocate portfolio based on current capital
            current_capital = starting_capital + sum(
                float(t.pnl) for t in all_trades
            )
            positions = portfolio_allocator.allocate(ranked, current_capital, mode)

            # Simulate trades for these positions
            day_trades = self._simulate_day_trades(
                positions=positions,
                trade_date=trade_date,
                hold_period_days=hold_period_days,
                backtest_id=backtest_id,
                db=db,
            )

            all_trades.extend(day_trades)

            # Update equity curve
            if day_trades:
                total_pnl = sum(float(t.pnl) for t in all_trades)
                equity_curve.append(
                    {"date": trade_date, "value": starting_capital + total_pnl}
                )

        # Commit all trades to database
        db.commit()

        # 4. Calculate final metrics
        results = self._calculate_metrics(all_trades, starting_capital, backtest_id)

        results["backtest_id"] = backtest_id
        results["mode"] = mode
        results["period"] = {"start": start_date, "end": end_date}
        results["hold_period_days"] = hold_period_days
        results["equity_curve"] = equity_curve

        logger.info(
            f"Backtest {backtest_id[:8]} complete | "
            f"Trades: {results['trades']['total']} | "
            f"P&L: ${results['metrics']['total_pnl']:,.2f} | "
            f"Return: {results['capital']['return_pct']:.1f}%"
        )

        return results

    def _group_signals_by_day(
        self, signals: List[Signal]
    ) -> Dict[str, List[Signal]]:
        """
        Group signals by date (YYYY-MM-DD).

        Args:
            signals: List of Signal objects

        Returns:
            Dictionary mapping date string to list of signals
        """
        grouped = {}
        for signal in signals:
            if signal.timestamp:
                date_key = signal.timestamp.strftime("%Y-%m-%d")
                if date_key not in grouped:
                    grouped[date_key] = []
                grouped[date_key].append(signal)
        return grouped

    def _simulate_day_trades(
        self,
        positions: List[Dict],
        trade_date: str,
        hold_period_days: int,
        backtest_id: str,
        db: Session,
    ) -> List[BacktestResult]:
        """
        Simulate trades for positions opened on a given day.

        For each position:
        1. Enter at signal.entry_price
        2. Check for stop-loss or take-profit during hold period
        3. Exit at appropriate price
        4. Calculate P&L
        5. Save BacktestResult to database

        Args:
            positions: List of allocated positions from PortfolioAllocator
            trade_date: Date the trades are opened (string)
            hold_period_days: Maximum days to hold
            backtest_id: UUID for this backtest run
            db: Database session

        Returns:
            List of BacktestResult records
        """
        trades = []
        entry_date = datetime.strptime(trade_date, "%Y-%m-%d").date()

        for position in positions:
            signal = position["signal"]
            shares = position["shares"]

            if shares == 0:
                continue

            # Entry price
            entry_price = float(signal.entry_price) if signal.entry_price else 100.0

            # Simulate hold period
            exit_price, exit_date, exit_reason = self._simulate_hold_period(
                signal=signal,
                entry_date=entry_date,
                entry_price=entry_price,
                hold_period_days=hold_period_days,
            )

            # Calculate P&L
            pnl = (exit_price - entry_price) * shares
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0

            trade_result = "WIN" if pnl > 0 else "LOSS"
            days_held = (exit_date - entry_date).days

            # Create BacktestResult record
            backtest_result = BacktestResult(
                backtest_id=backtest_id,
                signal_id=signal.id,
                entry_date=entry_date,
                exit_date=exit_date,
                entry_price=Decimal(str(round(entry_price, 2))),
                exit_price=Decimal(str(round(exit_price, 2))),
                shares=shares,
                pnl=Decimal(str(round(pnl, 2))),
                pnl_pct=Decimal(str(round(pnl_pct, 3))),
                trade_result=trade_result,
                days_held=days_held,
                exit_reason=exit_reason,
                position_type=position.get("position_type"),
                allocation_pct=Decimal(str(position.get("allocation_pct", 0))),
            )

            db.add(backtest_result)
            trades.append(backtest_result)

        return trades

    def _simulate_hold_period(
        self,
        signal: Signal,
        entry_date,
        entry_price: float,
        hold_period_days: int,
    ) -> tuple:
        """
        Simulate price movement during hold period.

        Checks for stop-loss and take-profit hits.
        Uses historical data when available, falls back to simulated movement.

        Args:
            signal: Signal with stop_loss and target_price
            entry_date: Date trade was opened
            entry_price: Entry price
            hold_period_days: Maximum hold period

        Returns:
            Tuple of (exit_price, exit_date, exit_reason)
        """
        stop_loss = float(signal.stop_loss) if signal.stop_loss else entry_price * 0.90
        target_price = float(signal.target_price) if signal.target_price else entry_price * 1.25

        # Try to get historical data for price simulation
        historical_data = market_data_service.get_historical_data(
            signal.ticker, days=hold_period_days + 5
        )

        # Build price lookup by date (if we have data)
        price_by_date = {}
        if historical_data:
            for bar in historical_data:
                price_by_date[bar["date"]] = bar

        exit_price = None
        exit_date = None
        exit_reason = None

        # Simulate each day of hold period
        for day_offset in range(1, hold_period_days + 1):
            check_date = entry_date + timedelta(days=day_offset)
            date_str = check_date.strftime("%Y-%m-%d")

            # Get price for this day
            if date_str in price_by_date:
                bar = price_by_date[date_str]
                day_low = bar["low"]
                day_high = bar["high"]
                day_close = bar["close"]
            else:
                # Simulate price movement if no historical data
                # Random walk with slight upward bias
                import random

                movement = random.uniform(-0.02, 0.025)
                day_close = entry_price * (1 + movement * (day_offset / hold_period_days))
                day_low = day_close * 0.99
                day_high = day_close * 1.01

            # Check stop-loss (hit if low <= stop_loss)
            if day_low <= stop_loss:
                exit_price = stop_loss
                exit_date = check_date
                exit_reason = "STOP_LOSS"
                break

            # Check take-profit (hit if high >= target)
            if day_high >= target_price:
                exit_price = target_price
                exit_date = check_date
                exit_reason = "TAKE_PROFIT"
                break

        # If no stop/target hit, exit at end of hold period
        if exit_price is None:
            exit_date = entry_date + timedelta(days=hold_period_days)
            exit_reason = "HOLD_PERIOD_END"

            # Use last available price or simulate
            end_date_str = exit_date.strftime("%Y-%m-%d")
            if end_date_str in price_by_date:
                exit_price = price_by_date[end_date_str]["close"]
            else:
                # Get current price as fallback
                current_price = market_data_service.get_current_price(signal.ticker)
                if current_price:
                    exit_price = current_price
                else:
                    # Last resort: assume slight movement from entry
                    import random

                    exit_price = entry_price * random.uniform(0.95, 1.10)

        return exit_price, exit_date, exit_reason

    def _calculate_metrics(
        self,
        trades: List[BacktestResult],
        starting_capital: float,
        backtest_id: str,
    ) -> Dict:
        """
        Calculate comprehensive backtest metrics.

        Args:
            trades: List of BacktestResult objects
            starting_capital: Initial capital
            backtest_id: Backtest identifier

        Returns:
            Dictionary with capital, trade, and performance metrics
        """
        if len(trades) == 0:
            return {
                "capital": {
                    "starting": starting_capital,
                    "ending": starting_capital,
                    "return_pct": 0.0,
                },
                "trades": {"total": 0, "wins": 0, "losses": 0, "win_rate": 0.0},
                "metrics": {
                    "total_pnl": 0.0,
                    "avg_gain": 0.0,
                    "avg_loss": 0.0,
                    "largest_win": 0.0,
                    "largest_loss": 0.0,
                    "profit_factor": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                    "avg_hold_days": 0,
                },
                "backtest_result_ids": [],
            }

        # Trade statistics
        total_trades = len(trades)
        wins = [t for t in trades if t.trade_result == "WIN"]
        losses = [t for t in trades if t.trade_result == "LOSS"]

        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / total_trades if total_trades > 0 else 0.0

        # P&L calculations
        total_pnl = sum(float(t.pnl) for t in trades)
        gross_profit = sum(float(t.pnl) for t in wins) if wins else 0.0
        gross_loss = abs(sum(float(t.pnl) for t in losses)) if losses else 0.0

        avg_gain = gross_profit / win_count if win_count > 0 else 0.0
        avg_loss = -gross_loss / loss_count if loss_count > 0 else 0.0

        largest_win = max(float(t.pnl) for t in wins) if wins else 0.0
        largest_loss = min(float(t.pnl) for t in losses) if losses else 0.0

        # Profit factor
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf") if gross_profit > 0 else 0.0

        # Capital metrics
        ending_capital = starting_capital + total_pnl
        return_pct = (total_pnl / starting_capital) * 100 if starting_capital > 0 else 0.0

        # Sharpe Ratio (simplified)
        returns = [float(t.pnl_pct) / 100 for t in trades]
        avg_return = sum(returns) / len(returns) if returns else 0.0
        std_return = (
            (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
            if len(returns) > 1
            else 0.0
        )
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0

        # Max drawdown (simplified - based on trade P&L sequence)
        cumulative = 0
        peak = 0
        max_dd = 0
        for trade in trades:
            cumulative += float(trade.pnl)
            if cumulative > peak:
                peak = cumulative
            drawdown = (peak - cumulative) / starting_capital if starting_capital > 0 else 0
            if drawdown > max_dd:
                max_dd = drawdown

        # Average hold days
        avg_hold_days = sum(t.days_held for t in trades) / total_trades if trades else 0

        return {
            "capital": {
                "starting": round(starting_capital, 2),
                "ending": round(ending_capital, 2),
                "return_pct": round(return_pct, 2),
            },
            "trades": {
                "total": total_trades,
                "wins": win_count,
                "losses": loss_count,
                "win_rate": round(win_rate, 3),
            },
            "metrics": {
                "total_pnl": round(total_pnl, 2),
                "avg_gain": round(avg_gain, 2),
                "avg_loss": round(avg_loss, 2),
                "largest_win": round(largest_win, 2),
                "largest_loss": round(largest_loss, 2),
                "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "Inf",
                "sharpe_ratio": round(sharpe_ratio, 3),
                "max_drawdown": round(max_dd, 4),
                "avg_hold_days": round(avg_hold_days, 1),
            },
            "backtest_result_ids": [t.id for t in trades if t.id],
        }


# Singleton instance
backtest_engine = BacktestEngine()
