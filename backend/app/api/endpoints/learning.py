"""
Learning System API Endpoints

Provides endpoints for:
- Viewing current agent weights
- Viewing weight history
- Viewing learning logs
- Triggering manual weight updates
- Manual weight overrides
- Viewing/updating system config
- Bias detection and reports
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.core.database import get_db
from app.services.learning_engine import LearningEngine
from app.services.meta_learning_engine import MetaLearningEngine, BiasType
from app.models.agent_weights_history import AgentWeightsHistory
from app.models.learning_log import LearningLog
from app.models.system_config import SystemConfig
from app.tasks.learning_tasks import (
    optimize_agent_weights_task,
    trigger_learning_update_task,
    check_critical_biases_task,
    manual_weight_override_task,
)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class WeightUpdate(BaseModel):
    """Request model for manual weight override."""

    agent_name: str = Field(
        ...,
        description="Name of the agent to update",
        examples=["ContrarianAgent"],
    )
    new_weight: float = Field(
        ...,
        description="New weight value (0.30 - 2.00)",
        ge=0.30,
        le=2.00,
    )
    reason: str = Field(
        ...,
        description="Reason for the weight change",
        min_length=10,
    )


class TriggerOptimizationRequest(BaseModel):
    """Request model for triggering optimization."""

    apply_weights: bool = Field(
        default=False,
        description="Whether to apply weight changes immediately",
    )
    force: bool = Field(
        default=False,
        description="Force update even if guardrails would block",
    )


class ConfigUpdate(BaseModel):
    """Request model for updating system config."""

    config_key: str = Field(
        ...,
        description="Configuration key to update",
    )
    config_value: str = Field(
        ...,
        description="New configuration value",
    )


class AgentWeightResponse(BaseModel):
    """Response model for agent weight."""

    agent_name: str
    weight: float
    win_rate_7d: Optional[float] = None
    win_rate_30d: Optional[float] = None
    win_rate_90d: Optional[float] = None
    trades_count_7d: Optional[int] = None
    trades_count_30d: Optional[int] = None
    trades_count_90d: Optional[int] = None
    last_updated: Optional[str] = None


class LearningLogResponse(BaseModel):
    """Response model for learning log entry."""

    id: int
    date: str
    event_type: str
    agent_name: Optional[str] = None
    metric_name: Optional[str] = None
    old_value: Optional[float] = None
    new_value: Optional[float] = None
    reasoning: Optional[str] = None
    bias_type: Optional[str] = None
    correction_applied: Optional[str] = None
    confidence_level: Optional[float] = None
    created_at: str


# ============================================================================
# Weight Endpoints
# ============================================================================


@router.get("/weights/current")
def get_current_weights(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get current agent weights.

    Returns the most recent weights for all agents.
    """
    # Get latest weight for each agent
    from sqlalchemy import func

    subquery = (
        db.query(
            AgentWeightsHistory.agent_name,
            func.max(AgentWeightsHistory.date).label("max_date")
        )
        .group_by(AgentWeightsHistory.agent_name)
        .subquery()
    )

    weights = (
        db.query(AgentWeightsHistory)
        .join(
            subquery,
            (AgentWeightsHistory.agent_name == subquery.c.agent_name) &
            (AgentWeightsHistory.date == subquery.c.max_date)
        )
        .all()
    )

    return {
        "status": "success",
        "weights": [
            {
                "agent_name": w.agent_name,
                "weight": float(w.weight),
                "win_rate_7d": float(w.win_rate_7d) if w.win_rate_7d else None,
                "win_rate_30d": float(w.win_rate_30d) if w.win_rate_30d else None,
                "win_rate_90d": float(w.win_rate_90d) if w.win_rate_90d else None,
                "trades_count_7d": w.trades_count_7d,
                "trades_count_30d": w.trades_count_30d,
                "trades_count_90d": w.trades_count_90d,
                "last_updated": w.date.isoformat() if w.date else None,
                "reasoning": w.reasoning,
            }
            for w in weights
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/weights/history")
def get_weight_history(
    agent_name: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get weight history for agents.

    Args:
        agent_name: Optional specific agent name
        days: Number of days of history to return
    """
    since = date.today() - timedelta(days=days)

    query = db.query(AgentWeightsHistory).filter(
        AgentWeightsHistory.date >= since
    )

    if agent_name:
        query = query.filter(AgentWeightsHistory.agent_name == agent_name)

    history = query.order_by(AgentWeightsHistory.date.desc()).all()

    return {
        "status": "success",
        "agent_name": agent_name,
        "period_days": days,
        "history": [
            {
                "id": h.id,
                "date": h.date.isoformat(),
                "agent_name": h.agent_name,
                "weight": float(h.weight),
                "win_rate_7d": float(h.win_rate_7d) if h.win_rate_7d else None,
                "win_rate_30d": float(h.win_rate_30d) if h.win_rate_30d else None,
                "win_rate_90d": float(h.win_rate_90d) if h.win_rate_90d else None,
                "trades_count_7d": h.trades_count_7d,
                "trades_count_30d": h.trades_count_30d,
                "trades_count_90d": h.trades_count_90d,
                "reasoning": h.reasoning,
            }
            for h in history
        ],
    }


@router.post("/weights/override")
def override_weight(
    request: WeightUpdate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Manually override an agent's weight.

    Used when human review determines a specific weight is needed.
    """
    learning_engine = LearningEngine(db)

    success = learning_engine.manual_override(
        agent_name=request.agent_name,
        new_weight=request.new_weight,
        reason=request.reason,
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to override weight for {request.agent_name}. Check agent name."
        )

    return {
        "status": "success",
        "message": f"Weight for {request.agent_name} set to {request.new_weight}",
        "agent_name": request.agent_name,
        "new_weight": request.new_weight,
        "reason": request.reason,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Optimization Endpoints
# ============================================================================


@router.post("/optimize/trigger")
def trigger_optimization(
    request: TriggerOptimizationRequest = TriggerOptimizationRequest(),
) -> Dict[str, Any]:
    """
    Trigger an on-demand optimization run.

    Can be used to manually trigger weight optimization outside
    the scheduled daily run.

    Args:
        apply_weights: Whether to apply changes (requires authorization)
        force: Force update even if guardrails block
    """
    # Trigger async task
    task = trigger_learning_update_task.delay(
        apply_weights=request.apply_weights,
        force=request.force,
    )

    return {
        "status": "triggered",
        "task_id": task.id,
        "apply_weights": request.apply_weights,
        "force": request.force,
        "message": "Optimization task queued",
    }


@router.get("/optimize/preview")
def preview_optimization(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Preview what an optimization run would do.

    Shows proposed weight changes without applying them.
    Useful for human review before approving changes.
    """
    learning_engine = LearningEngine(db)

    # Calculate current state
    performances = learning_engine.calculate_rolling_performance()
    current_weights = learning_engine._get_current_weights()
    proposed_weights = learning_engine.calculate_new_weights(performances, current_weights)

    # Check guardrails
    is_safe = learning_engine.is_safe_to_apply(current_weights, proposed_weights)

    # Get bias report
    bias_report = learning_engine.meta_engine.detect_all_biases()

    return {
        "status": "preview",
        "current_weights": current_weights,
        "proposed_weights": proposed_weights,
        "weight_changes": {
            agent: {
                "old": current_weights.get(agent, 1.0),
                "new": proposed_weights.get(agent, 1.0),
                "change": proposed_weights.get(agent, 1.0) - current_weights.get(agent, 1.0),
            }
            for agent in set(current_weights.keys()) | set(proposed_weights.keys())
        },
        "performances": {
            agent: {
                "win_rate_7d": perf.win_rate_7d,
                "win_rate_30d": perf.win_rate_30d,
                "win_rate_90d": perf.win_rate_90d,
                "blended_score": perf.blended_score,
            }
            for agent, perf in performances.items()
        },
        "biases_detected": [
            {
                "type": b.bias_type.value,
                "agent": b.agent_name,
                "severity": b.severity,
                "description": b.description,
            }
            for b in bias_report.biases
        ],
        "safe_to_apply": is_safe,
        "requires_human_review": learning_engine.human_review_required,
        "auto_learning_enabled": learning_engine.auto_learning_enabled,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/optimize/apply")
def apply_optimization(
    force: bool = False,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Apply optimization immediately.

    This will calculate new weights and apply them now.

    Args:
        force: Force update even if guardrails would block
    """
    learning_engine = LearningEngine(db)

    # Run optimization
    result = learning_engine.optimize_daily()

    if not result.weights_updated and not force:
        return {
            "status": "not_applied",
            "reason": result.reasoning,
            "requires_human_review": learning_engine.human_review_required,
            "proposed_changes": result.weight_changes,
            "message": "Weights not updated. Use force=true to override.",
        }

    # If force and not updated, try manual update
    if not result.weights_updated and force:
        performances = learning_engine.calculate_rolling_performance()
        current_weights = learning_engine._get_current_weights()
        proposed_weights = learning_engine.calculate_new_weights(performances, current_weights)

        learning_engine._apply_weights(
            proposed_weights,
            "Forced manual update via API",
            performances
        )

        return {
            "status": "force_applied",
            "new_weights": proposed_weights,
            "message": "Weights force-applied via API",
        }

    return {
        "status": "applied",
        "weights_updated": result.weights_updated,
        "weight_changes": result.weight_changes,
        "biases_detected": [b.bias_type.value for b in result.biases_detected],
        "confidence_level": result.confidence_level,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Bias Detection Endpoints
# ============================================================================


@router.get("/biases/check")
def check_biases(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Check for current biases in the learning system.

    Detects:
    - OVERFITTING: Low sample significance
    - RECENCY: Over-weighting recent performance
    - THRASHING: Rapid weight oscillations
    - REGIME_BLINDNESS: Ignoring market regime changes
    """
    learning_engine = LearningEngine(db)
    bias_report = learning_engine.meta_engine.detect_all_biases()

    return {
        "status": "success",
        "check_date": date.today().isoformat(),
        "biases_detected": len(bias_report.biases),
        "biases": [
            {
                "type": b.bias_type.value,
                "agent": b.agent_name,
                "severity": b.severity,
                "description": b.description,
                "correction_available": b.correction is not None,
            }
            for b in bias_report.biases
        ],
        "recommendations": bias_report.recommendations,
        "overall_confidence": bias_report.overall_confidence,
    }


@router.post("/biases/trigger-check")
def trigger_bias_check() -> Dict[str, Any]:
    """
    Trigger an async bias check task.

    Useful for running bias checks in the background.
    """
    task = check_critical_biases_task.delay()

    return {
        "status": "triggered",
        "task_id": task.id,
        "message": "Bias check task queued",
    }


# ============================================================================
# Learning Log Endpoints
# ============================================================================


@router.get("/logs")
def get_learning_logs(
    event_type: Optional[str] = None,
    agent_name: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get learning system logs.

    Filters:
        event_type: WEIGHT_UPDATE, BIAS_DETECTED, CORRECTION_APPLIED, REGIME_SHIFT, FREEZE, ALERT
        agent_name: Filter by specific agent
        days: Number of days of history
        limit: Max records to return
        offset: Pagination offset
    """
    since = date.today() - timedelta(days=days)

    query = db.query(LearningLog).filter(LearningLog.date >= since)

    if event_type:
        query = query.filter(LearningLog.event_type == event_type)

    if agent_name:
        query = query.filter(LearningLog.agent_name == agent_name)

    total = query.count()

    logs = (
        query
        .order_by(LearningLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "status": "success",
        "total": total,
        "offset": offset,
        "limit": limit,
        "filters": {
            "event_type": event_type,
            "agent_name": agent_name,
            "days": days,
        },
        "logs": [
            {
                "id": log.id,
                "date": log.date.isoformat(),
                "event_type": log.event_type,
                "agent_name": log.agent_name,
                "metric_name": log.metric_name,
                "old_value": float(log.old_value) if log.old_value else None,
                "new_value": float(log.new_value) if log.new_value else None,
                "reasoning": log.reasoning,
                "bias_type": log.bias_type,
                "correction_applied": log.correction_applied,
                "confidence_level": float(log.confidence_level) if log.confidence_level else None,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


@router.get("/logs/summary")
def get_log_summary(days: int = 30, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get summary of learning log events.

    Returns counts by event type and agent.
    """
    from sqlalchemy import func

    since = date.today() - timedelta(days=days)

    # Count by event type
    event_counts = (
        db.query(
            LearningLog.event_type,
            func.count(LearningLog.id).label("count")
        )
        .filter(LearningLog.date >= since)
        .group_by(LearningLog.event_type)
        .all()
    )

    # Count by agent
    agent_counts = (
        db.query(
            LearningLog.agent_name,
            func.count(LearningLog.id).label("count")
        )
        .filter(LearningLog.date >= since)
        .filter(LearningLog.agent_name.isnot(None))
        .group_by(LearningLog.agent_name)
        .all()
    )

    # Count biases by type
    bias_counts = (
        db.query(
            LearningLog.bias_type,
            func.count(LearningLog.id).label("count")
        )
        .filter(LearningLog.date >= since)
        .filter(LearningLog.bias_type.isnot(None))
        .group_by(LearningLog.bias_type)
        .all()
    )

    return {
        "status": "success",
        "period_days": days,
        "by_event_type": {row.event_type: row.count for row in event_counts},
        "by_agent": {row.agent_name: row.count for row in agent_counts if row.agent_name},
        "by_bias_type": {row.bias_type: row.count for row in bias_counts if row.bias_type},
    }


# ============================================================================
# Config Endpoints
# ============================================================================


@router.get("/config")
def get_config(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get all learning system configuration.
    """
    configs = db.query(SystemConfig).all()

    return {
        "status": "success",
        "config": {
            c.config_key: {
                "value": c.config_value,
                "description": c.description,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            }
            for c in configs
        },
    }


@router.get("/config/{config_key}")
def get_config_value(config_key: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get a specific configuration value.
    """
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail=f"Config key '{config_key}' not found")

    return {
        "config_key": config.config_key,
        "config_value": config.config_value,
        "description": config.description,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


@router.put("/config/{config_key}")
def update_config(
    config_key: str,
    request: ConfigUpdate,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Update a configuration value.

    Note: Changes to AUTO_LEARNING_ENABLED and HUMAN_REVIEW_REQUIRED
    affect system behavior immediately.
    """
    config = db.query(SystemConfig).filter(
        SystemConfig.config_key == config_key
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail=f"Config key '{config_key}' not found")

    old_value = config.config_value
    config.config_value = request.config_value
    db.commit()
    db.refresh(config)

    # Log the change
    log_entry = LearningLog(
        date=date.today(),
        event_type="CONFIG_UPDATE",
        metric_name=config_key,
        reasoning=f"Config updated from '{old_value}' to '{request.config_value}'",
    )
    db.add(log_entry)
    db.commit()

    return {
        "status": "success",
        "config_key": config.config_key,
        "old_value": old_value,
        "new_value": config.config_value,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None,
    }


# ============================================================================
# Status Endpoint
# ============================================================================


@router.get("/status")
def get_learning_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get overall learning system status.

    Returns summary of:
    - Current weights
    - Recent optimization results
    - System configuration
    - Active biases
    """
    learning_engine = LearningEngine(db)

    # Get current weights
    current_weights = learning_engine._get_current_weights()

    # Get latest optimization log
    latest_opt = (
        db.query(LearningLog)
        .filter(LearningLog.event_type.in_(["DAILY_OPTIMIZATION", "WEIGHT_UPDATE"]))
        .order_by(LearningLog.created_at.desc())
        .first()
    )

    # Count recent events
    from sqlalchemy import func
    yesterday = date.today() - timedelta(days=1)

    events_24h = (
        db.query(func.count(LearningLog.id))
        .filter(LearningLog.date >= yesterday)
        .scalar()
    )

    # Check for active biases
    bias_report = learning_engine.meta_engine.detect_all_biases()

    return {
        "status": "healthy" if not bias_report.biases else "biases_detected",
        "auto_learning_enabled": learning_engine.auto_learning_enabled,
        "human_review_required": learning_engine.human_review_required,
        "current_weights": current_weights,
        "last_optimization": {
            "date": latest_opt.date.isoformat() if latest_opt else None,
            "event_type": latest_opt.event_type if latest_opt else None,
            "confidence": float(latest_opt.confidence_level) if latest_opt and latest_opt.confidence_level else None,
        },
        "events_last_24h": events_24h,
        "active_biases": len(bias_report.biases),
        "bias_types": [b.bias_type.value for b in bias_report.biases],
        "timestamp": datetime.utcnow().isoformat(),
    }
