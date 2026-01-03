"""
Market Data Model
Cached market data from external APIs
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, BigInteger, UniqueConstraint
from app.core.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    source = Column(String(50))  # polygon, finnhub, alphavantage

    __table_args__ = (
        UniqueConstraint(
            "ticker", "timestamp", "source", name="uix_market_data_ticker_time_source"
        ),
    )

    def __repr__(self):
        return f"<MarketData(ticker={self.ticker}, close={self.close}, source={self.source})>"
