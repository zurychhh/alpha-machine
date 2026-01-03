"""
Performance Model
Daily portfolio performance tracking
"""

from sqlalchemy import Column, Integer, Numeric, Date
from app.core.database import Base


class Performance(Base):
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    portfolio_value = Column(Numeric(12, 2), nullable=False)
    cash_balance = Column(Numeric(12, 2))
    daily_pnl = Column(Numeric(10, 2))
    total_pnl = Column(Numeric(10, 2))
    num_positions = Column(Integer)
    win_rate = Column(Numeric(5, 2))
    sharpe_ratio = Column(Numeric(5, 2))
    max_drawdown = Column(Numeric(5, 2))

    def __repr__(self):
        return f"<Performance(date={self.date}, value={self.portfolio_value})>"
