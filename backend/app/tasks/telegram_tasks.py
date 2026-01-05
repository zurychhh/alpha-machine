"""
Telegram Tasks - Scheduled notifications for Alpha Machine

Tasks:
- send_daily_signal_summary_task: Daily signal summary at 8:30 AM EST
- send_signal_alert_task: Real-time alert for high-confidence signals
- check_and_alert_high_confidence: Check for high-confidence signals and alert
"""

from celery import shared_task
from typing import Dict, List, Any
import logging
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models.signal import Signal
from app.services.telegram_bot import get_telegram_service
from app.core.config import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.telegram_tasks.send_daily_signal_summary_task",
    max_retries=2,
    default_retry_delay=60,
)
def send_daily_signal_summary_task(self) -> Dict[str, Any]:
    """
    Send daily signal summary to Telegram at 8:30 AM EST.

    Collects all signals generated in the last 24 hours and sends
    a formatted summary to the configured Telegram chat.

    Returns:
        Dict with task results
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.warning("Telegram not configured, skipping daily summary")
        return {"status": "skipped", "reason": "telegram_not_configured"}

    if not settings.TELEGRAM_CHAT_ID:
        logger.warning("Telegram chat ID not configured, skipping daily summary")
        return {"status": "skipped", "reason": "chat_id_not_configured"}

    db = SessionLocal()
    result = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }

    try:
        # Get signals from the last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        signals = (
            db.query(Signal)
            .filter(Signal.timestamp >= since)
            .order_by(Signal.confidence.desc())
            .all()
        )

        # Convert to dict format for telegram service
        signal_list = [
            {
                "ticker": s.ticker,
                "signal_type": s.signal_type,
                "confidence": s.confidence / 5.0,  # Convert 1-5 to 0-1
                "entry_price": float(s.entry_price) if s.entry_price else None,
                "target_price": float(s.target_price) if s.target_price else None,
                "stop_loss": float(s.stop_loss) if s.stop_loss else None,
            }
            for s in signals
        ]

        # Send summary
        telegram_service = get_telegram_service()
        success = telegram_service.send_daily_summary_sync(signal_list)

        result["status"] = "sent" if success else "failed"
        result["signal_count"] = len(signal_list)
        result["buy_count"] = len([s for s in signals if s.signal_type == "BUY"])
        result["sell_count"] = len([s for s in signals if s.signal_type == "SELL"])
        result["hold_count"] = len([s for s in signals if s.signal_type == "HOLD"])

        logger.info(
            f"Daily summary sent: {len(signal_list)} signals "
            f"(BUY: {result['buy_count']}, SELL: {result['sell_count']}, HOLD: {result['hold_count']})"
        )

    except Exception as e:
        logger.error(f"Failed to send daily summary: {e}")
        result["status"] = "error"
        result["error"] = str(e)
        raise self.retry(exc=e)

    finally:
        db.close()

    return result


@shared_task(name="app.tasks.telegram_tasks.send_signal_alert_task")
def send_signal_alert_task(signal_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a real-time signal alert to Telegram.

    Called when a high-confidence signal is generated.

    Args:
        signal_data: Signal dictionary with ticker, signal_type, confidence, etc.

    Returns:
        Dict with task results
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return {"status": "skipped", "reason": "telegram_not_configured"}

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "ticker": signal_data.get("ticker"),
        "status": "pending",
    }

    try:
        telegram_service = get_telegram_service()
        success = telegram_service.send_signal_alert_sync(signal_data)

        result["status"] = "sent" if success else "failed"
        result["signal_type"] = signal_data.get("signal_type")
        result["confidence"] = signal_data.get("confidence")

        if success:
            logger.info(
                f"Signal alert sent: {signal_data.get('ticker')} "
                f"{signal_data.get('signal_type')} ({signal_data.get('confidence')})"
            )

    except Exception as e:
        logger.error(f"Failed to send signal alert: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


@shared_task(
    bind=True,
    name="app.tasks.telegram_tasks.check_and_alert_high_confidence",
    max_retries=1,
)
def check_and_alert_high_confidence(
    self,
    min_confidence: int = 4,
    hours: int = 1,
) -> Dict[str, Any]:
    """
    Check for recent high-confidence signals and send alerts.

    Runs periodically to catch signals that might have been missed.

    Args:
        min_confidence: Minimum confidence level (1-5 scale, 4 = 80%)
        hours: Look back period in hours

    Returns:
        Dict with task results
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return {"status": "skipped", "reason": "telegram_not_configured"}

    db = SessionLocal()
    result = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "alerts_sent": 0,
        "status": "pending",
    }

    try:
        # Find high-confidence signals that haven't been alerted
        since = datetime.utcnow() - timedelta(hours=hours)
        signals = (
            db.query(Signal)
            .filter(Signal.timestamp >= since)
            .filter(Signal.confidence >= min_confidence)
            .filter(Signal.signal_type.in_(["BUY", "SELL"]))
            .order_by(Signal.confidence.desc())
            .all()
        )

        telegram_service = get_telegram_service()

        for signal in signals:
            signal_data = {
                "ticker": signal.ticker,
                "signal_type": signal.signal_type,
                "confidence": signal.confidence / 5.0,  # Convert to 0-1
                "entry_price": float(signal.entry_price) if signal.entry_price else None,
                "target_price": float(signal.target_price) if signal.target_price else None,
                "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            }

            if telegram_service.should_alert(signal_data):
                success = telegram_service.send_signal_alert_sync(signal_data)
                if success:
                    result["alerts_sent"] += 1
                    logger.info(
                        f"High-confidence alert sent: {signal.ticker} "
                        f"{signal.signal_type} (conf: {signal.confidence})"
                    )

        result["status"] = "completed"
        result["signals_checked"] = len(signals)

    except Exception as e:
        logger.error(f"High-confidence check failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    finally:
        db.close()

    return result


def trigger_signal_alert(signal: Signal) -> bool:
    """
    Trigger an immediate alert for a high-confidence signal.

    Called by signal_service after saving a new signal.

    Args:
        signal: Signal database object

    Returns:
        True if alert was sent successfully
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False

    # Only alert for high-confidence BUY/SELL signals
    if signal.confidence < 4 or signal.signal_type == "HOLD":
        return False

    signal_data = {
        "ticker": signal.ticker,
        "signal_type": signal.signal_type,
        "confidence": signal.confidence / 5.0,  # Convert to 0-1
        "entry_price": float(signal.entry_price) if signal.entry_price else None,
        "target_price": float(signal.target_price) if signal.target_price else None,
        "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
    }

    # Trigger async task
    send_signal_alert_task.delay(signal_data)
    return True
