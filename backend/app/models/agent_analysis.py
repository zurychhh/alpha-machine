"""
Agent Analysis Model
Individual agent recommendations for each signal
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AgentAnalysis(Base):
    __tablename__ = "agent_analysis"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)  # contrarian, growth, multimodal, predictor
    recommendation = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Integer, nullable=False)  # 1-5
    reasoning = Column(Text, nullable=False)  # Why this recommendation
    data_used = Column(JSONB)  # What data was analyzed
    timestamp = Column(DateTime, server_default=func.now())

    # Relationships
    signal = relationship("Signal", back_populates="agent_analyses")

    def __repr__(self):
        return f"<AgentAnalysis(agent={self.agent_name}, rec={self.recommendation})>"
