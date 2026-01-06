"""
Learning Log Model
Records all learning system events: weight updates, bias detection, corrections, alerts.
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class LearningLog(Base):
    __tablename__ = "learning_log"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)

    # Event classification
    event_type = Column(String(30), nullable=False, index=True)
    # Values: WEIGHT_UPDATE, BIAS_DETECTED, CORRECTION_APPLIED,
    #         REGIME_SHIFT, FREEZE, ALERT

    agent_name = Column(String(50), nullable=True, index=True)
    metric_name = Column(String(50), nullable=True)

    # Value changes
    old_value = Column(Numeric(10, 4), nullable=True)
    new_value = Column(Numeric(10, 4), nullable=True)

    # Detailed reasoning
    reasoning = Column(Text)

    # Bias information
    bias_type = Column(String(30), nullable=True)
    # Values: OVERFITTING, RECENCY, THRASHING, REGIME_BLINDNESS

    correction_applied = Column(Text, nullable=True)
    confidence_level = Column(Numeric(3, 2), nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return (
            f"<LearningLog(date={self.date}, type={self.event_type}, "
            f"agent={self.agent_name})>"
        )

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "event_type": self.event_type,
            "agent_name": self.agent_name,
            "metric_name": self.metric_name,
            "old_value": float(self.old_value) if self.old_value else None,
            "new_value": float(self.new_value) if self.new_value else None,
            "reasoning": self.reasoning,
            "bias_type": self.bias_type,
            "correction_applied": self.correction_applied,
            "confidence_level": float(self.confidence_level) if self.confidence_level else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
