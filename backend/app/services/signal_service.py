"""
Signal Service - CRUD operations for trading signals
Handles signal persistence, risk parameters, and history
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.models.signal import Signal
from app.models.agent_analysis import AgentAnalysis
from app.agents.signal_generator import ConsensusSignal, PositionSize
from app.agents.base_agent import AgentSignal, SignalType
from app.core.config import settings

logger = logging.getLogger(__name__)


def _trigger_telegram_alert(signal: Signal) -> bool:
    """
    Trigger Telegram alert for high-confidence signals.

    Only alerts for BUY/SELL signals with confidence >= 4 (80%).
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False

    # Only alert for high-confidence BUY/SELL signals
    if signal.confidence < 4 or signal.signal_type == "HOLD":
        return False

    try:
        from app.tasks.telegram_tasks import send_signal_alert_task

        signal_data = {
            "ticker": signal.ticker,
            "signal_type": signal.signal_type,
            "confidence": signal.confidence / 5.0,  # Convert 1-5 to 0-1
            "entry_price": float(signal.entry_price) if signal.entry_price else None,
            "target_price": float(signal.target_price) if signal.target_price else None,
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
        }

        # Trigger async task
        send_signal_alert_task.delay(signal_data)
        logger.info(f"Telegram alert triggered for {signal.ticker}")
        return True
    except Exception as e:
        logger.warning(f"Failed to trigger Telegram alert: {e}")
        return False


class SignalService:
    """
    Service for managing trading signals.

    Handles:
    - Signal persistence to database
    - Risk parameter calculation (stop loss, target price)
    - Position sizing
    - Signal history and retrieval
    """

    # Risk parameters
    STOP_LOSS_PERCENT = 0.10  # 10% below entry
    TARGET_PERCENT = 0.25  # 25% above entry
    MAX_POSITION_PERCENT = 0.10  # Max 10% of portfolio per position

    # Position size multipliers
    POSITION_MULTIPLIERS = {
        PositionSize.NONE: 0.0,
        PositionSize.SMALL: 0.25,
        PositionSize.MEDIUM: 0.50,
        PositionSize.NORMAL: 1.0,
        PositionSize.LARGE: 1.5,
    }

    def __init__(self, db: Session):
        """
        Initialize signal service with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.logger = logging.getLogger("signal_service")

    def save_signal(
        self,
        consensus: ConsensusSignal,
        entry_price: float,
        portfolio_value: float = 100000.0,
    ) -> Signal:
        """
        Save a consensus signal to the database.

        Args:
            consensus: ConsensusSignal from SignalGenerator
            entry_price: Current market price for entry
            portfolio_value: Total portfolio value for position sizing

        Returns:
            Saved Signal database object
        """
        # Calculate risk parameters
        stop_loss = self._calculate_stop_loss(entry_price, consensus.signal)
        target_price = self._calculate_target_price(entry_price, consensus.signal)
        position_size = self._calculate_shares(
            entry_price, portfolio_value, consensus.position_size
        )

        # Map signal type to database format
        signal_type = self._map_signal_type(consensus.signal)

        # Map confidence to 1-5 scale
        confidence_score = self._map_confidence(consensus.confidence)

        # Create signal record
        signal = Signal(
            ticker=consensus.ticker,
            signal_type=signal_type,
            confidence=confidence_score,
            entry_price=Decimal(str(round(entry_price, 2))),
            target_price=Decimal(str(round(target_price, 2))),
            stop_loss=Decimal(str(round(stop_loss, 2))),
            position_size=position_size,
            status="PENDING",
            notes=consensus.reasoning[:500] if consensus.reasoning else None,
        )

        self.db.add(signal)
        self.db.flush()  # Get the signal ID

        # Save individual agent analyses
        self._save_agent_analyses(signal.id, consensus.agent_signals)

        self.db.commit()
        self.db.refresh(signal)

        self.logger.info(
            f"Saved signal {signal.id}: {signal.ticker} {signal.signal_type} "
            f"@ ${entry_price} (confidence: {signal.confidence})"
        )

        # Trigger Telegram alert for high-confidence signals
        _trigger_telegram_alert(signal)

        return signal

    def _save_agent_analyses(
        self, signal_id: int, agent_signals: List[AgentSignal]
    ) -> None:
        """Save individual agent analyses to database."""
        for agent_signal in agent_signals:
            # AgentSignal uses 'factors' dict, map to data_used for database
            data_used = getattr(agent_signal, "factors", {}) or {}
            analysis = AgentAnalysis(
                signal_id=signal_id,
                agent_name=agent_signal.agent_name,
                recommendation=agent_signal.signal.value,
                confidence=self._map_confidence(agent_signal.confidence),
                reasoning=agent_signal.reasoning[:1000] if agent_signal.reasoning else "",
                data_used=data_used,
            )
            self.db.add(analysis)

    def _calculate_stop_loss(self, entry_price: float, signal: SignalType) -> float:
        """
        Calculate stop loss price.

        For BUY signals: entry * (1 - STOP_LOSS_PERCENT)
        For SELL signals: entry * (1 + STOP_LOSS_PERCENT)
        """
        if signal in (SignalType.BUY, SignalType.STRONG_BUY):
            return entry_price * (1 - self.STOP_LOSS_PERCENT)
        elif signal in (SignalType.SELL, SignalType.STRONG_SELL):
            return entry_price * (1 + self.STOP_LOSS_PERCENT)
        else:
            return entry_price

    def _calculate_target_price(self, entry_price: float, signal: SignalType) -> float:
        """
        Calculate target price.

        For BUY signals: entry * (1 + TARGET_PERCENT)
        For SELL signals: entry * (1 - TARGET_PERCENT)
        """
        if signal in (SignalType.BUY, SignalType.STRONG_BUY):
            return entry_price * (1 + self.TARGET_PERCENT)
        elif signal in (SignalType.SELL, SignalType.STRONG_SELL):
            return entry_price * (1 - self.TARGET_PERCENT)
        else:
            return entry_price

    def _calculate_shares(
        self,
        entry_price: float,
        portfolio_value: float,
        position_size: PositionSize,
    ) -> int:
        """
        Calculate number of shares for position.

        Respects MAX_POSITION_PERCENT and scales by position size recommendation.
        """
        if position_size == PositionSize.NONE or entry_price <= 0:
            return 0

        # Max position value = portfolio * max_percent * multiplier
        multiplier = self.POSITION_MULTIPLIERS.get(position_size, 1.0)
        max_position_value = portfolio_value * self.MAX_POSITION_PERCENT * multiplier

        # Calculate shares
        shares = int(max_position_value / entry_price)
        return max(0, shares)

    def _map_signal_type(self, signal: SignalType) -> str:
        """Map SignalType enum to database string."""
        mapping = {
            SignalType.STRONG_BUY: "BUY",
            SignalType.BUY: "BUY",
            SignalType.HOLD: "HOLD",
            SignalType.SELL: "SELL",
            SignalType.STRONG_SELL: "SELL",
        }
        return mapping.get(signal, "HOLD")

    def _map_confidence(self, confidence: float) -> int:
        """Map confidence (0.0-1.0) to 1-5 scale."""
        if confidence >= 0.8:
            return 5
        elif confidence >= 0.6:
            return 4
        elif confidence >= 0.4:
            return 3
        elif confidence >= 0.2:
            return 2
        else:
            return 1

    def get_signal(self, signal_id: int) -> Optional[Signal]:
        """
        Get a signal by ID with agent analyses.

        Args:
            signal_id: Signal database ID

        Returns:
            Signal with agent_analyses loaded, or None if not found
        """
        return (
            self.db.query(Signal)
            .filter(Signal.id == signal_id)
            .first()
        )

    def get_signals(
        self,
        ticker: Optional[str] = None,
        signal_type: Optional[str] = None,
        status: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Signal]:
        """
        Get signals with optional filtering.

        Args:
            ticker: Filter by ticker symbol
            signal_type: Filter by signal type (BUY, SELL, HOLD)
            status: Filter by status (PENDING, APPROVED, EXECUTED, CLOSED)
            days: Number of days to look back
            limit: Maximum number of signals to return
            offset: Offset for pagination

        Returns:
            List of matching signals
        """
        query = self.db.query(Signal)

        # Apply filters
        if ticker:
            query = query.filter(Signal.ticker == ticker.upper())

        if signal_type:
            query = query.filter(Signal.signal_type == signal_type.upper())

        if status:
            query = query.filter(Signal.status == status.upper())

        # Time filter
        since = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Signal.timestamp >= since)

        # Order and paginate
        query = query.order_by(desc(Signal.timestamp))
        query = query.offset(offset).limit(limit)

        return query.all()

    def get_signals_by_ticker(self, ticker: str, limit: int = 10) -> List[Signal]:
        """Get recent signals for a specific ticker."""
        return self.get_signals(ticker=ticker, limit=limit)

    def get_pending_signals(self) -> List[Signal]:
        """Get all pending signals awaiting approval."""
        return self.get_signals(status="PENDING", days=7)

    def update_signal_status(
        self,
        signal_id: int,
        status: str,
        pnl: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Optional[Signal]:
        """
        Update signal status.

        Args:
            signal_id: Signal database ID
            status: New status (PENDING, APPROVED, EXECUTED, CLOSED)
            pnl: Profit/Loss if closing
            notes: Additional notes

        Returns:
            Updated signal or None if not found
        """
        signal = self.get_signal(signal_id)
        if not signal:
            return None

        signal.status = status.upper()

        if status.upper() == "EXECUTED":
            signal.executed_at = datetime.utcnow()
        elif status.upper() == "CLOSED":
            signal.closed_at = datetime.utcnow()
            if pnl is not None:
                signal.pnl = Decimal(str(round(pnl, 2)))

        if notes:
            signal.notes = notes

        self.db.commit()
        self.db.refresh(signal)

        self.logger.info(f"Updated signal {signal_id} status to {status}")
        return signal

    def approve_signal(self, signal_id: int) -> Optional[Signal]:
        """Approve a pending signal for execution."""
        return self.update_signal_status(signal_id, "APPROVED")

    def execute_signal(self, signal_id: int) -> Optional[Signal]:
        """Mark a signal as executed."""
        return self.update_signal_status(signal_id, "EXECUTED")

    def close_signal(
        self, signal_id: int, pnl: float, notes: Optional[str] = None
    ) -> Optional[Signal]:
        """Close a signal with P&L result."""
        return self.update_signal_status(signal_id, "CLOSED", pnl=pnl, notes=notes)

    def signal_to_dict(self, signal: Signal) -> Dict[str, Any]:
        """
        Convert Signal to dictionary with agent analyses.

        Args:
            signal: Signal database object

        Returns:
            Dictionary representation
        """
        result = {
            "id": signal.id,
            "ticker": signal.ticker,
            "signal_type": signal.signal_type,
            "confidence": signal.confidence,
            "entry_price": float(signal.entry_price) if signal.entry_price else None,
            "target_price": float(signal.target_price) if signal.target_price else None,
            "stop_loss": float(signal.stop_loss) if signal.stop_loss else None,
            "position_size": signal.position_size,
            "status": signal.status,
            "timestamp": signal.timestamp.isoformat() if signal.timestamp else None,
            "executed_at": signal.executed_at.isoformat() if signal.executed_at else None,
            "closed_at": signal.closed_at.isoformat() if signal.closed_at else None,
            "pnl": float(signal.pnl) if signal.pnl else None,
            "notes": signal.notes,
            "agent_analyses": [],
        }

        # Add agent analyses if loaded
        if signal.agent_analyses:
            result["agent_analyses"] = [
                {
                    "id": aa.id,
                    "agent_name": aa.agent_name,
                    "recommendation": aa.recommendation,
                    "confidence": aa.confidence,
                    "reasoning": aa.reasoning,
                    "data_used": aa.data_used,
                    "timestamp": aa.timestamp.isoformat() if aa.timestamp else None,
                }
                for aa in signal.agent_analyses
            ]

        return result

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get signal statistics for the specified period.

        Returns:
            Dict with counts, win rate, average P&L, etc.
        """
        since = datetime.utcnow() - timedelta(days=days)

        signals = (
            self.db.query(Signal)
            .filter(Signal.timestamp >= since)
            .all()
        )

        total = len(signals)
        if total == 0:
            return {
                "period_days": days,
                "total_signals": 0,
                "by_type": {},
                "by_status": {},
                "win_rate": None,
                "average_pnl": None,
            }

        # Count by type
        by_type = {}
        for s in signals:
            by_type[s.signal_type] = by_type.get(s.signal_type, 0) + 1

        # Count by status
        by_status = {}
        for s in signals:
            by_status[s.status] = by_status.get(s.status, 0) + 1

        # Calculate win rate for closed signals
        closed = [s for s in signals if s.status == "CLOSED" and s.pnl is not None]
        if closed:
            winners = [s for s in closed if s.pnl > 0]
            win_rate = len(winners) / len(closed)
            avg_pnl = sum(float(s.pnl) for s in closed) / len(closed)
        else:
            win_rate = None
            avg_pnl = None

        return {
            "period_days": days,
            "total_signals": total,
            "by_type": by_type,
            "by_status": by_status,
            "closed_signals": len(closed),
            "win_rate": round(win_rate, 3) if win_rate is not None else None,
            "average_pnl": round(avg_pnl, 2) if avg_pnl is not None else None,
        }


# Singleton pattern for service access
_signal_service: Optional[SignalService] = None


def get_signal_service(db: Session) -> SignalService:
    """Get or create signal service instance."""
    return SignalService(db)
