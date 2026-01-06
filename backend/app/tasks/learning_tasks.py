"""
Learning Tasks - Scheduled learning system optimization for Alpha Machine

Tasks:
- optimize_agent_weights_task: Daily agent weight optimization at 00:00 EST
- trigger_learning_update_task: On-demand learning update
- check_critical_biases_task: Check for critical biases and alert
"""

from celery import shared_task
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime, date

from app.core.database import SessionLocal
from app.services.learning_engine import LearningEngine, OptimizationResult
from app.services.meta_learning_engine import BiasType
from app.models.learning_log import LearningLog
from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_telegram_alert(message: str, alert_type: str = "info") -> bool:
    """
    Send a Telegram alert for learning system events.

    Args:
        message: Alert message text
        alert_type: Type of alert (info, warning, critical)

    Returns:
        True if sent successfully
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured, skipping alert")
        return False

    try:
        from app.services.telegram_bot import get_telegram_service

        # Format message with emoji based on type
        emoji_map = {
            "info": "📊",
            "warning": "⚠️",
            "critical": "🚨",
        }
        emoji = emoji_map.get(alert_type, "📊")

        formatted_message = f"{emoji} **Learning System Alert**\n\n{message}"

        telegram_service = get_telegram_service()
        return telegram_service.send_message_sync(formatted_message)
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
        return False


def _format_optimization_summary(result: OptimizationResult) -> str:
    """Format optimization result for logging and alerting."""
    lines = [
        f"📈 **Agent Weight Optimization - {result.date}**",
        "",
        f"**Status:** {'✅ Weights Updated' if result.weights_updated else '⏸️ No Changes (Review Required)'}",
        "",
    ]

    # Add bias detection summary
    if result.biases_detected:
        lines.append("**Biases Detected:**")
        for bias in result.biases_detected:
            lines.append(f"  • {bias.bias_type.value}: {bias.description}")
        lines.append("")
    else:
        lines.append("**Biases Detected:** None")
        lines.append("")

    # Add weight changes
    if result.weight_changes:
        lines.append("**Weight Changes:**")
        for agent, change in result.weight_changes.items():
            direction = "↑" if change.get("change", 0) > 0 else "↓" if change.get("change", 0) < 0 else "→"
            lines.append(
                f"  • {agent}: {change.get('old', 1.0):.2f} {direction} {change.get('new', 1.0):.2f}"
            )
        lines.append("")

    # Add confidence
    lines.append(f"**Confidence Level:** {result.confidence_level:.1%}")

    # Add reasoning
    if result.reasoning:
        lines.append(f"\n**Reasoning:** {result.reasoning[:200]}...")

    return "\n".join(lines)


@shared_task(
    bind=True,
    name="app.tasks.learning_tasks.optimize_agent_weights_task",
    max_retries=2,
    default_retry_delay=300,
)
def optimize_agent_weights_task(self) -> Dict[str, Any]:
    """
    Daily agent weight optimization task.

    Runs at 00:00 EST (06:00 UTC) to:
    1. Calculate rolling performance for each agent
    2. Detect and correct biases using meta-learning
    3. Update weights if auto-learning is enabled
    4. Log all results to learning_log
    5. Send Telegram alert if critical biases detected

    Returns:
        Dict with optimization results
    """
    db = SessionLocal()
    task_result = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
        "weights_updated": False,
        "biases_detected": [],
        "alerts_sent": 0,
    }

    try:
        logger.info("Starting daily agent weight optimization")

        # Initialize learning engine
        learning_engine = LearningEngine(db)

        # Run daily optimization
        result: OptimizationResult = learning_engine.optimize_daily()

        # Populate task result
        task_result["status"] = "completed"
        task_result["weights_updated"] = result.weights_updated
        task_result["confidence_level"] = result.confidence_level
        task_result["reasoning"] = result.reasoning

        # Process biases
        if result.biases_detected:
            task_result["biases_detected"] = [
                {
                    "type": bias.bias_type.value,
                    "agent": bias.agent_name,
                    "description": bias.description,
                    "severity": bias.severity,
                }
                for bias in result.biases_detected
            ]

            # Check for critical biases
            critical_biases = [
                b for b in result.biases_detected
                if b.severity >= 0.8
            ]

            if critical_biases:
                # Send Telegram alert for critical biases
                alert_message = (
                    f"🚨 **Critical Bias Detected**\n\n"
                    f"Date: {result.date}\n\n"
                )
                for bias in critical_biases:
                    alert_message += (
                        f"• **{bias.bias_type.value}** on {bias.agent_name}\n"
                        f"  Severity: {bias.severity:.0%}\n"
                        f"  {bias.description}\n\n"
                    )
                alert_message += "⚠️ Human review recommended."

                if _send_telegram_alert(alert_message, alert_type="critical"):
                    task_result["alerts_sent"] += 1

        # Process weight changes
        if result.weight_changes:
            task_result["weight_changes"] = result.weight_changes

        # Log summary to learning_log
        summary_log = LearningLog(
            date=date.today(),
            event_type="DAILY_OPTIMIZATION",
            reasoning=_format_optimization_summary(result),
            confidence_level=result.confidence_level,
        )
        db.add(summary_log)
        db.commit()

        # Send success notification if weights were updated
        if result.weights_updated:
            summary_message = _format_optimization_summary(result)
            _send_telegram_alert(summary_message, alert_type="info")
            task_result["alerts_sent"] += 1

        logger.info(
            f"Daily optimization completed: weights_updated={result.weights_updated}, "
            f"biases_detected={len(result.biases_detected)}, "
            f"confidence={result.confidence_level:.2f}"
        )

    except Exception as e:
        logger.error(f"Daily optimization task failed: {e}")
        task_result["status"] = "error"
        task_result["error"] = str(e)

        # Log error to learning_log
        try:
            error_log = LearningLog(
                date=date.today(),
                event_type="ERROR",
                reasoning=f"Daily optimization failed: {str(e)}",
            )
            db.add(error_log)
            db.commit()
        except Exception:
            pass

        # Send error alert
        _send_telegram_alert(
            f"Daily optimization failed: {str(e)}",
            alert_type="critical"
        )

        raise self.retry(exc=e)

    finally:
        db.close()

    return task_result


@shared_task(
    name="app.tasks.learning_tasks.trigger_learning_update_task",
)
def trigger_learning_update_task(
    apply_weights: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """
    On-demand learning update task.

    Can be triggered manually to:
    1. Calculate new proposed weights
    2. Optionally apply them immediately (if authorized)

    Args:
        apply_weights: Whether to apply weight changes
        force: Force update even if guardrails would block

    Returns:
        Dict with update results
    """
    db = SessionLocal()
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
    }

    try:
        logger.info(f"Triggered learning update (apply={apply_weights}, force={force})")

        learning_engine = LearningEngine(db)

        # Calculate rolling performance
        performances = learning_engine.calculate_rolling_performance()
        result["agent_performances"] = {
            agent: {
                "win_rate_7d": perf.win_rate_7d,
                "win_rate_30d": perf.win_rate_30d,
                "win_rate_90d": perf.win_rate_90d,
                "blended_score": perf.blended_score,
            }
            for agent, perf in performances.items()
        }

        # Calculate new weights
        current_weights = learning_engine._get_current_weights()
        proposed_weights = learning_engine.calculate_new_weights(
            performances, current_weights
        )
        result["proposed_weights"] = proposed_weights

        # Run bias detection
        bias_report = learning_engine.meta_engine.detect_all_biases()
        result["biases"] = [
            {"type": b.bias_type.value, "agent": b.agent_name}
            for b in bias_report.biases
        ]

        # Check if safe to apply
        is_safe = learning_engine.is_safe_to_apply(
            current_weights, proposed_weights
        )
        result["safe_to_apply"] = is_safe

        if apply_weights:
            if is_safe or force:
                # Apply weights
                learning_engine._apply_weights(
                    proposed_weights,
                    f"Manual update (force={force})",
                    performances
                )
                result["weights_applied"] = True
                result["status"] = "weights_updated"

                # Log the update
                update_log = LearningLog(
                    date=date.today(),
                    event_type="MANUAL_UPDATE",
                    reasoning=f"Manual weight update triggered (force={force})",
                )
                db.add(update_log)
                db.commit()
            else:
                result["weights_applied"] = False
                result["status"] = "blocked_by_guardrails"
                result["message"] = "Guardrails prevented update. Use force=True to override."
        else:
            result["weights_applied"] = False
            result["status"] = "preview_only"

        logger.info(f"Learning update completed: {result['status']}")

    except Exception as e:
        logger.error(f"Learning update failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    finally:
        db.close()

    return result


@shared_task(
    name="app.tasks.learning_tasks.check_critical_biases_task",
)
def check_critical_biases_task() -> Dict[str, Any]:
    """
    Check for critical biases and send alerts.

    Can be run periodically to monitor for bias accumulation.

    Returns:
        Dict with bias check results
    """
    db = SessionLocal()
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "pending",
        "biases_found": 0,
        "critical_biases": 0,
    }

    try:
        learning_engine = LearningEngine(db)

        # Run bias detection
        bias_report = learning_engine.meta_engine.detect_all_biases()

        result["biases_found"] = len(bias_report.biases)
        result["biases"] = [
            {
                "type": b.bias_type.value,
                "agent": b.agent_name,
                "severity": b.severity,
                "description": b.description,
            }
            for b in bias_report.biases
        ]

        # Count critical biases (severity >= 0.8)
        critical = [b for b in bias_report.biases if b.severity >= 0.8]
        result["critical_biases"] = len(critical)

        if critical:
            # Send alert
            alert_message = f"🔍 **Bias Check Found {len(critical)} Critical Issues**\n\n"
            for bias in critical:
                alert_message += (
                    f"• **{bias.bias_type.value}**\n"
                    f"  Agent: {bias.agent_name}\n"
                    f"  Severity: {bias.severity:.0%}\n\n"
                )
            alert_message += "Consider running manual weight optimization."

            _send_telegram_alert(alert_message, alert_type="warning")

        result["status"] = "completed"

    except Exception as e:
        logger.error(f"Bias check failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    finally:
        db.close()

    return result


@shared_task(
    name="app.tasks.learning_tasks.manual_weight_override_task",
)
def manual_weight_override_task(
    agent_name: str,
    new_weight: float,
    reason: str,
) -> Dict[str, Any]:
    """
    Manually override an agent's weight.

    Used when human review determines a specific weight is needed.

    Args:
        agent_name: Name of the agent to update
        new_weight: New weight value (0.30 - 2.00)
        reason: Reason for the override

    Returns:
        Dict with override results
    """
    db = SessionLocal()
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent_name": agent_name,
        "new_weight": new_weight,
        "status": "pending",
    }

    try:
        learning_engine = LearningEngine(db)

        # Validate weight bounds
        if new_weight < 0.30 or new_weight > 2.00:
            result["status"] = "error"
            result["error"] = f"Weight must be between 0.30 and 2.00, got {new_weight}"
            return result

        # Apply override
        success = learning_engine.manual_override(
            agent_name=agent_name,
            new_weight=new_weight,
            reason=reason,
        )

        if success:
            result["status"] = "applied"
            result["message"] = f"Weight for {agent_name} set to {new_weight}"

            # Send notification
            _send_telegram_alert(
                f"Manual weight override applied:\n"
                f"Agent: {agent_name}\n"
                f"New Weight: {new_weight}\n"
                f"Reason: {reason}",
                alert_type="info"
            )
        else:
            result["status"] = "failed"
            result["error"] = "Override failed - check agent name"

    except Exception as e:
        logger.error(f"Manual override failed: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    finally:
        db.close()

    return result
