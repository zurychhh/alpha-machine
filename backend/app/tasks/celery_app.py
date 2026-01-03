"""
Celery Application Configuration
Background task processing for Alpha Machine

Tasks:
- Data fetching (every 5 minutes during market hours)
- Sentiment analysis (every 30 minutes)
- Signal generation (daily at 9am EST)
"""

from celery import Celery
from celery.schedules import crontab
import os

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "alpha_machine",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=[
        "app.tasks.data_tasks",
        "app.tasks.signal_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/New_York",  # EST for market hours
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour

    # Beat scheduler settings
    beat_schedule={
        # Fetch market data every 5 minutes during market hours (9:30 AM - 4:00 PM EST)
        "fetch-market-data-5min": {
            "task": "app.tasks.data_tasks.fetch_market_data_task",
            "schedule": 300.0,  # Every 5 minutes
            "options": {"queue": "data"},
        },

        # Fetch sentiment every 30 minutes
        "fetch-sentiment-30min": {
            "task": "app.tasks.data_tasks.fetch_sentiment_task",
            "schedule": 1800.0,  # Every 30 minutes
            "options": {"queue": "data"},
        },

        # Generate signals daily at 9:00 AM EST (before market open)
        "generate-signals-daily": {
            "task": "app.tasks.signal_tasks.generate_daily_signals_task",
            "schedule": crontab(hour=9, minute=0),
            "options": {"queue": "signals"},
        },

        # Generate mid-day signals at 12:00 PM EST
        "generate-signals-midday": {
            "task": "app.tasks.signal_tasks.generate_daily_signals_task",
            "schedule": crontab(hour=12, minute=0),
            "options": {"queue": "signals"},
        },

        # End-of-day analysis at 4:30 PM EST (after market close)
        "analyze-signals-eod": {
            "task": "app.tasks.signal_tasks.analyze_signal_performance_task",
            "schedule": crontab(hour=16, minute=30),
            "options": {"queue": "signals"},
        },
    },

    # Task routing
    task_routes={
        "app.tasks.data_tasks.*": {"queue": "data"},
        "app.tasks.signal_tasks.*": {"queue": "signals"},
    },

    # Default queue
    task_default_queue="default",
)


# Optional: Task events for monitoring
celery_app.conf.task_send_sent_event = True
celery_app.conf.worker_send_task_events = True


def is_market_hours() -> bool:
    """
    Check if current time is within US market hours.

    Market hours: 9:30 AM - 4:00 PM EST, Monday-Friday
    """
    from datetime import datetime
    import pytz

    est = pytz.timezone("America/New_York")
    now = datetime.now(est)

    # Check if it's a weekday
    if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False

    # Check if within market hours
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now <= market_close


# Export for convenience
app = celery_app
