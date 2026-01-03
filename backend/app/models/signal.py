"""
Signal Model
Generated buy/sell signals from agent consensus
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    ticker = Column(String(10), ForeignKey("watchlist.ticker"), nullable=False, index=True)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Integer, nullable=False)  # 1-5 (number of agents agreeing)
    entry_price = Column(Numeric(10, 2))
    target_price = Column(Numeric(10, 2))
    stop_loss = Column(Numeric(10, 2))
    position_size = Column(Integer)  # Number of shares
    status = Column(
        String(20), default="PENDING", index=True
    )  # PENDING, APPROVED, EXECUTED, CLOSED
    executed_at = Column(DateTime)
    closed_at = Column(DateTime)
    pnl = Column(Numeric(10, 2))
    notes = Column(Text)

    # Relationships
    watchlist_item = relationship("Watchlist", back_populates="signals")
    agent_analyses = relationship("AgentAnalysis", back_populates="signal")

    def __repr__(self):
        return (
            f"<Signal(ticker={self.ticker}, type={self.signal_type}, confidence={self.confidence})>"
        )
