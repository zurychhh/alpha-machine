"""
Watchlist Model
AI stocks being monitored by the system
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Watchlist(Base):
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(100))
    sector = Column(String(50))
    tier = Column(Integer)  # 1=Core, 2=Growth, 3=Tactical
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    signals = relationship("Signal", back_populates="watchlist_item")
    portfolio_positions = relationship("Portfolio", back_populates="watchlist_item")
    sentiment_data = relationship("SentimentData", back_populates="watchlist_item")

    def __repr__(self):
        return f"<Watchlist(ticker={self.ticker}, tier={self.tier})>"
