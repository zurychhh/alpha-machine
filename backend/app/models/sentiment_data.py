"""
Sentiment Data Model
Social media and news sentiment data
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SentimentData(Base):
    __tablename__ = "sentiment_data"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), ForeignKey("watchlist.ticker"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    source = Column(String(50), nullable=False)  # reddit, twitter, news
    sentiment_score = Column(Numeric(3, 2))  # -1 to +1
    mention_count = Column(Integer)
    raw_data = Column(JSONB)

    # Relationships
    watchlist_item = relationship("Watchlist", back_populates="sentiment_data")

    def __repr__(self):
        return f"<SentimentData(ticker={self.ticker}, source={self.source}, score={self.sentiment_score})>"
