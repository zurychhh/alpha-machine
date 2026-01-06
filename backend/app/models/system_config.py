"""
System Config Model
Stores configuration settings for the learning system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SystemConfig(key={self.config_key}, value={self.config_value})>"

    def to_dict(self):
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_default_configs(cls):
        """Returns default configuration values for the learning system."""
        return [
            {
                "config_key": "AUTO_LEARNING_ENABLED",
                "config_value": "false",
                "description": "Enable automatic weight optimization without human review"
            },
            {
                "config_key": "HUMAN_REVIEW_REQUIRED",
                "config_value": "true",
                "description": "Require human review before applying weight changes"
            },
            {
                "config_key": "MIN_CONFIDENCE_FOR_AUTO",
                "config_value": "0.80",
                "description": "Minimum confidence level for automatic weight application"
            },
            {
                "config_key": "MAX_WEIGHT_CHANGE_DAILY",
                "config_value": "0.10",
                "description": "Maximum allowed weight change per day (10%)"
            },
            {
                "config_key": "WEIGHT_MIN_BOUND",
                "config_value": "0.30",
                "description": "Minimum allowed agent weight"
            },
            {
                "config_key": "WEIGHT_MAX_BOUND",
                "config_value": "2.00",
                "description": "Maximum allowed agent weight"
            },
            {
                "config_key": "LEARNING_TIMEFRAME_WEIGHTS",
                "config_value": '{"7d": 0.4, "30d": 0.4, "90d": 0.2}',
                "description": "Weights for different time periods in performance calculation"
            },
            {
                "config_key": "FREEZE_DURATION_DAYS",
                "config_value": "3",
                "description": "Number of days to freeze weights when thrashing detected"
            },
        ]
