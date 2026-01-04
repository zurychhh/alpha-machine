"""
BacktestResult Model - Stores individual trade results from backtesting.

Each record represents one simulated trade within a backtest run.
Multiple trades can belong to the same backtest_id.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)

    # Backtest run identifier (UUID per backtest run)
    backtest_id = Column(String(50), nullable=False, index=True)

    # Link to the signal that triggered this trade
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, index=True)

    # Trade timing
    entry_date = Column(Date, nullable=False)
    exit_date = Column(Date, nullable=False)

    # Trade prices
    entry_price = Column(Numeric(10, 2), nullable=False)
    exit_price = Column(Numeric(10, 2), nullable=False)

    # Position details
    shares = Column(Integer, nullable=False)

    # Profit & Loss
    pnl = Column(Numeric(10, 2), nullable=False)  # Dollar P&L
    pnl_pct = Column(Numeric(7, 3), nullable=False)  # Percentage return

    # Trade outcome
    trade_result = Column(String(10), nullable=False)  # WIN or LOSS
    days_held = Column(Integer, nullable=False)
    exit_reason = Column(
        String(20)
    )  # STOP_LOSS, TAKE_PROFIT, HOLD_PERIOD_END, ERROR

    # Portfolio allocation info
    position_type = Column(String(20))  # CORE, SATELLITE, EQUAL
    allocation_pct = Column(Numeric(5, 3))  # e.g., 0.60 = 60%

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return (
            f"<BacktestResult(backtest={self.backtest_id[:8]}, "
            f"signal={self.signal_id}, result={self.trade_result}, "
            f"pnl=${float(self.pnl):.2f})>"
        )
