"""
Tasks Module - Celery background tasks for Alpha Machine

Includes:
- celery_app: Celery application configuration
- data_tasks: Market data and sentiment fetching tasks
- signal_tasks: Signal generation and analysis tasks
- learning_tasks: Self-learning weight optimization tasks
"""

from app.tasks.celery_app import celery_app, app, is_market_hours
from app.tasks.data_tasks import (
    fetch_market_data_task,
    fetch_sentiment_task,
    fetch_single_ticker_data,
    refresh_all_data,
)
from app.tasks.signal_tasks import (
    generate_daily_signals_task,
    generate_signal_for_ticker,
    analyze_signal_performance_task,
    generate_high_confidence_alerts,
)
from app.tasks.learning_tasks import (
    optimize_agent_weights_task,
    trigger_learning_update_task,
    check_critical_biases_task,
    manual_weight_override_task,
)

__all__ = [
    # Celery app
    "celery_app",
    "app",
    "is_market_hours",
    # Data tasks
    "fetch_market_data_task",
    "fetch_sentiment_task",
    "fetch_single_ticker_data",
    "refresh_all_data",
    # Signal tasks
    "generate_daily_signals_task",
    "generate_signal_for_ticker",
    "analyze_signal_performance_task",
    "generate_high_confidence_alerts",
    # Learning tasks
    "optimize_agent_weights_task",
    "trigger_learning_update_task",
    "check_critical_biases_task",
    "manual_weight_override_task",
]
