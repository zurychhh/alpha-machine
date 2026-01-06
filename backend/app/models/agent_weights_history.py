"""
Agent Weights History Model
Tracks historical changes to agent weights over time for learning system.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class AgentWeightsHistory(Base):
    __tablename__ = "agent_weights_history"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    weight = Column(Numeric(4, 2), nullable=False)

    # Performance metrics for different time periods
    win_rate_7d = Column(Numeric(5, 2))
    win_rate_30d = Column(Numeric(5, 2))
    win_rate_90d = Column(Numeric(5, 2))
    trades_count_7d = Column(Integer, default=0)
    trades_count_30d = Column(Integer, default=0)
    trades_count_90d = Column(Integer, default=0)

    # Reasoning for weight change
    reasoning = Column(Text)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return (
            f"<AgentWeightsHistory(date={self.date}, agent={self.agent_name}, "
            f"weight={self.weight})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "agent_name": self.agent_name,
            "weight": float(self.weight) if self.weight else None,
            "win_rate_7d": float(self.win_rate_7d) if self.win_rate_7d else None,
            "win_rate_30d": float(self.win_rate_30d) if self.win_rate_30d else None,
            "win_rate_90d": float(self.win_rate_90d) if self.win_rate_90d else None,
            "trades_count_7d": self.trades_count_7d,
            "trades_count_30d": self.trades_count_30d,
            "trades_count_90d": self.trades_count_90d,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
