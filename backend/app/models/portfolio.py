"""
Portfolio Model
Current positions held in the portfolio
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Portfolio(Base):
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), ForeignKey("watchlist.ticker"), nullable=False)
    shares = Column(Integer, nullable=False)
    avg_cost = Column(Numeric(10, 2), nullable=False)
    current_price = Column(Numeric(10, 2))
    market_value = Column(Numeric(10, 2))
    unrealized_pnl = Column(Numeric(10, 2))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    watchlist_item = relationship("Watchlist", back_populates="portfolio_positions")

    def __repr__(self):
        return f"<Portfolio(ticker={self.ticker}, shares={self.shares})>"
