"""
Telegram Bot Service - Notifications for Alpha Machine
Handles signal alerts, daily summaries, and user commands.
Uses direct Telegram API calls for reliability.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    Telegram bot service for Alpha Machine notifications.

    Features:
    - Real-time alerts for high-confidence signals (≥75%)
    - Daily signal summary at 8:30 AM EST
    - User commands: /signals, /watchlist, /status
    """

    BASE_URL = "https://api.telegram.org/bot{token}/{method}"

    # Confidence threshold for real-time alerts (75% = 0.75)
    ALERT_CONFIDENCE_THRESHOLD = 0.75

    # Signal type emojis
    SIGNAL_EMOJIS = {
        "BUY": "🟢",
        "SELL": "🔴",
        "HOLD": "🟡",
    }

    # Confidence stars
    CONFIDENCE_STARS = {
        5: "⭐⭐⭐⭐⭐",
        4: "⭐⭐⭐⭐",
        3: "⭐⭐⭐",
        2: "⭐⭐",
        1: "⭐",
    }

    def __init__(self):
        """Initialize Telegram bot service."""
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.logger = logging.getLogger("telegram_bot")

        if not self.token:
            self.logger.warning("TELEGRAM_BOT_TOKEN not configured")

    def _get_url(self, method: str) -> str:
        """Get Telegram API URL for a method."""
        return self.BASE_URL.format(token=self.token, method=method)

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
    ) -> bool:
        """
        Send a message to Telegram chat.

        Args:
            text: Message text (supports HTML formatting)
            chat_id: Target chat ID (uses default if not provided)
            parse_mode: Message parse mode (HTML or Markdown)

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.token:
            self.logger.error("Bot token not configured")
            return False

        target_chat = chat_id or self.chat_id
        if not target_chat:
            self.logger.error("No chat_id configured")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._get_url("sendMessage"),
                    json={
                        "chat_id": target_chat,
                        "text": text,
                        "parse_mode": parse_mode,
                    },
                    timeout=10.0,
                )
                result = response.json()

                if result.get("ok"):
                    self.logger.info(f"Message sent to chat {target_chat}")
                    return True
                else:
                    self.logger.error(f"Telegram API error: {result}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    def send_message_sync(
        self,
        text: str,
        chat_id: Optional[str] = None,
    ) -> bool:
        """
        Synchronous wrapper for send_message.
        Used in non-async contexts (e.g., Celery tasks).
        """
        import httpx

        if not self.token:
            return False

        target_chat = chat_id or self.chat_id
        if not target_chat:
            return False

        try:
            response = httpx.post(
                self._get_url("sendMessage"),
                json={
                    "chat_id": target_chat,
                    "text": text,
                    "parse_mode": "HTML",
                },
                timeout=10.0,
            )
            return response.json().get("ok", False)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            return False

    async def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send real-time alert for a high-confidence signal.
        """
        ticker = signal_data.get("ticker", "UNKNOWN")
        signal_type = signal_data.get("signal_type", "HOLD")
        confidence = signal_data.get("confidence", 0)
        entry_price = signal_data.get("entry_price")
        target_price = signal_data.get("target_price")
        stop_loss = signal_data.get("stop_loss")

        # Convert confidence to percentage
        conf_percent = confidence * 100 if confidence <= 1 else confidence * 20

        emoji = self.SIGNAL_EMOJIS.get(signal_type, "⚪")
        conf_int = int(confidence) if confidence > 1 else int(confidence * 5)
        stars = self.CONFIDENCE_STARS.get(conf_int, "")

        # Format prices safely
        entry_str = f"${entry_price:.2f}" if entry_price else "N/A"
        target_str = f"${target_price:.2f}" if target_price else "N/A"
        stop_str = f"${stop_loss:.2f}" if stop_loss else "N/A"

        message = f"""🚨 <b>ALPHA MACHINE SIGNAL ALERT</b> 🚨

{emoji} <b>{ticker}</b> - <b>{signal_type}</b>

📊 <b>Confidence:</b> {conf_percent:.1f}% {stars}
💰 <b>Entry Price:</b> {entry_str}
🎯 <b>Target:</b> {target_str}
🛑 <b>Stop Loss:</b> {stop_str}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}

<i>This signal met the ≥75% confidence threshold</i>"""

        return await self.send_message(message)

    def send_signal_alert_sync(self, signal_data: Dict[str, Any]) -> bool:
        """Synchronous wrapper for send_signal_alert."""
        ticker = signal_data.get("ticker", "UNKNOWN")
        signal_type = signal_data.get("signal_type", "HOLD")
        confidence = signal_data.get("confidence", 0)
        entry_price = signal_data.get("entry_price")
        target_price = signal_data.get("target_price")
        stop_loss = signal_data.get("stop_loss")

        conf_percent = confidence * 100 if confidence <= 1 else confidence * 20
        emoji = self.SIGNAL_EMOJIS.get(signal_type, "⚪")
        conf_int = int(confidence) if confidence > 1 else int(confidence * 5)
        stars = self.CONFIDENCE_STARS.get(conf_int, "")

        entry_str = f"${entry_price:.2f}" if entry_price else "N/A"
        target_str = f"${target_price:.2f}" if target_price else "N/A"
        stop_str = f"${stop_loss:.2f}" if stop_loss else "N/A"

        message = f"""🚨 <b>ALPHA MACHINE SIGNAL ALERT</b> 🚨

{emoji} <b>{ticker}</b> - <b>{signal_type}</b>

📊 <b>Confidence:</b> {conf_percent:.1f}% {stars}
💰 <b>Entry Price:</b> {entry_str}
🎯 <b>Target:</b> {target_str}
🛑 <b>Stop Loss:</b> {stop_str}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}

<i>This signal met the ≥75% confidence threshold</i>"""

        return self.send_message_sync(message)

    async def send_daily_summary(self, signals: List[Dict[str, Any]]) -> bool:
        """Send daily signal summary."""
        if not signals:
            message = f"""📊 <b>ALPHA MACHINE DAILY SUMMARY</b>

No signals generated today.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}"""
            return await self.send_message(message)

        # Group signals by type
        buy_signals = [s for s in signals if s.get("signal_type") == "BUY"]
        sell_signals = [s for s in signals if s.get("signal_type") == "SELL"]
        hold_signals = [s for s in signals if s.get("signal_type") == "HOLD"]

        # Build signal list
        signal_lines = []
        for signal in sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True):
            ticker = signal.get("ticker", "???")
            signal_type = signal.get("signal_type", "HOLD")
            confidence = signal.get("confidence", 0)
            conf_percent = confidence * 100 if confidence <= 1 else confidence * 20
            emoji = self.SIGNAL_EMOJIS.get(signal_type, "⚪")
            signal_lines.append(f"  {emoji} <b>{ticker}</b>: {signal_type} ({conf_percent:.0f}%)")

        signal_list = "\n".join(signal_lines[:15])

        message = f"""📊 <b>ALPHA MACHINE DAILY SUMMARY</b>

📈 <b>Today's Signals:</b>
{signal_list}

📊 <b>Summary:</b>
  🟢 BUY: {len(buy_signals)}
  🔴 SELL: {len(sell_signals)}
  🟡 HOLD: {len(hold_signals)}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}"""

        return await self.send_message(message)

    def send_daily_summary_sync(self, signals: List[Dict[str, Any]]) -> bool:
        """Synchronous wrapper for send_daily_summary."""
        if not signals:
            message = f"""📊 <b>ALPHA MACHINE DAILY SUMMARY</b>

No signals generated today.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}"""
            return self.send_message_sync(message)

        buy_signals = [s for s in signals if s.get("signal_type") == "BUY"]
        sell_signals = [s for s in signals if s.get("signal_type") == "SELL"]
        hold_signals = [s for s in signals if s.get("signal_type") == "HOLD"]

        signal_lines = []
        for signal in sorted(signals, key=lambda x: x.get("confidence", 0), reverse=True):
            ticker = signal.get("ticker", "???")
            signal_type = signal.get("signal_type", "HOLD")
            confidence = signal.get("confidence", 0)
            conf_percent = confidence * 100 if confidence <= 1 else confidence * 20
            emoji = self.SIGNAL_EMOJIS.get(signal_type, "⚪")
            signal_lines.append(f"  {emoji} <b>{ticker}</b>: {signal_type} ({conf_percent:.0f}%)")

        signal_list = "\n".join(signal_lines[:15])

        message = f"""📊 <b>ALPHA MACHINE DAILY SUMMARY</b>

📈 <b>Today's Signals:</b>
{signal_list}

📊 <b>Summary:</b>
  🟢 BUY: {len(buy_signals)}
  🔴 SELL: {len(sell_signals)}
  🟡 HOLD: {len(hold_signals)}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}"""

        return self.send_message_sync(message)

    async def process_webhook(self, update_data: Dict[str, Any]) -> Optional[str]:
        """
        Process incoming webhook update from Telegram.
        Returns response message if command was handled.
        """
        message = update_data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id")

        if not chat_id or not text:
            return None

        # Handle commands
        if text.startswith("/start"):
            return await self._handle_start(chat_id)
        elif text.startswith("/signals"):
            return await self._handle_signals(chat_id)
        elif text.startswith("/watchlist"):
            return await self._handle_watchlist(chat_id)
        elif text.startswith("/status"):
            return await self._handle_status(chat_id)
        elif text.startswith("/help"):
            return await self._handle_help(chat_id)

        return None

    async def _handle_start(self, chat_id: int) -> str:
        """Handle /start command."""
        message = f"""🤖 <b>Welcome to Alpha Machine Bot!</b>

Your AI-powered stock trading assistant.

<b>Your Chat ID:</b> <code>{chat_id}</code>
(Add this to TELEGRAM_CHAT_ID in your environment)

<b>Available Commands:</b>
/signals - View recent trading signals
/watchlist - View monitored stocks
/status - Check system status
/help - Show this help message

<i>You'll receive real-time alerts for signals with ≥75% confidence.</i>"""

        await self.send_message(message, chat_id=str(chat_id))
        return "start_handled"

    async def _handle_signals(self, chat_id: int) -> str:
        """Handle /signals command - show recent signals."""
        from app.core.database import SessionLocal
        from app.services.signal_service import SignalService

        try:
            db = SessionLocal()
            service = SignalService(db)
            signals = service.get_signals(days=1, limit=10)
            db.close()

            if not signals:
                await self.send_message(
                    "📊 No signals in the last 24 hours.",
                    chat_id=str(chat_id),
                )
                return "signals_empty"

            lines = ["📊 <b>Recent Signals (Last 24h):</b>\n"]
            for signal in signals:
                emoji = self.SIGNAL_EMOJIS.get(signal.signal_type, "⚪")
                conf_percent = signal.confidence * 20
                lines.append(
                    f"  {emoji} <b>{signal.ticker}</b>: {signal.signal_type} "
                    f"({conf_percent:.0f}%) @ ${float(signal.entry_price):.2f}"
                )

            await self.send_message("\n".join(lines), chat_id=str(chat_id))
            return "signals_sent"

        except Exception as e:
            self.logger.error(f"Error in /signals: {e}")
            await self.send_message(
                "❌ Error fetching signals. Please try again.",
                chat_id=str(chat_id),
            )
            return "signals_error"

    async def _handle_watchlist(self, chat_id: int) -> str:
        """Handle /watchlist command - show monitored stocks."""
        from app.core.database import SessionLocal
        from app.models.watchlist import Watchlist

        try:
            db = SessionLocal()
            stocks = db.query(Watchlist).filter(Watchlist.active == True).all()
            db.close()

            if not stocks:
                await self.send_message(
                    "📋 Watchlist is empty.",
                    chat_id=str(chat_id),
                )
                return "watchlist_empty"

            lines = ["📋 <b>Watchlist:</b>\n"]
            for stock in stocks:
                tier_emoji = "⭐" if stock.tier and stock.tier <= 2 else ""
                lines.append(f"  • <b>{stock.ticker}</b> {tier_emoji}")

            lines.append(f"\n<i>Total: {len(stocks)} stocks</i>")

            await self.send_message("\n".join(lines), chat_id=str(chat_id))
            return "watchlist_sent"

        except Exception as e:
            self.logger.error(f"Error in /watchlist: {e}")
            await self.send_message(
                "❌ Error fetching watchlist. Please try again.",
                chat_id=str(chat_id),
            )
            return "watchlist_error"

    async def _handle_status(self, chat_id: int) -> str:
        """Handle /status command - show system status."""
        from app.core.database import SessionLocal
        from app.models.signal import Signal
        from app.models.watchlist import Watchlist

        try:
            db = SessionLocal()

            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            total_signals = db.query(Signal).count()
            today_signals = (
                db.query(Signal)
                .filter(Signal.timestamp >= today_start)
                .count()
            )
            active_stocks = (
                db.query(Watchlist)
                .filter(Watchlist.active == True)
                .count()
            )
            db.close()

            message = f"""🖥️ <b>Alpha Machine Status</b>

✅ <b>System:</b> Online
📊 <b>Total Signals:</b> {total_signals}
📈 <b>Today's Signals:</b> {today_signals}
📋 <b>Active Stocks:</b> {active_stocks}

🤖 <b>AI Agents:</b>
  • ContrarianAgent (GPT-4o) ✅
  • GrowthAgent (Claude) ✅
  • MultiModalAgent (Gemini) ✅
  • PredictorAgent (Local) ✅

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}"""

            await self.send_message(message, chat_id=str(chat_id))
            return "status_sent"

        except Exception as e:
            self.logger.error(f"Error in /status: {e}")
            await self.send_message(
                "❌ Error fetching status. Please try again.",
                chat_id=str(chat_id),
            )
            return "status_error"

    async def _handle_help(self, chat_id: int) -> str:
        """Handle /help command."""
        message = """🤖 <b>Alpha Machine Bot - Help</b>

<b>Commands:</b>
/signals - View recent trading signals (last 24h)
/watchlist - View monitored stocks
/status - Check system status
/help - Show this help message

<b>Automatic Notifications:</b>
• Real-time alerts for signals with ≥75% confidence
• Daily summary at 8:30 AM EST

<b>Signal Types:</b>
🟢 BUY - Recommended to buy
🔴 SELL - Recommended to sell
🟡 HOLD - Maintain current position

<b>Confidence Levels:</b>
⭐⭐⭐⭐⭐ 80-100% - Very high confidence
⭐⭐⭐⭐ 60-80% - High confidence
⭐⭐⭐ 40-60% - Moderate confidence

<i>For support, visit the Alpha Machine dashboard.</i>"""

        await self.send_message(message, chat_id=str(chat_id))
        return "help_sent"

    def should_alert(self, signal_data: Dict[str, Any]) -> bool:
        """Check if a signal should trigger a real-time alert."""
        confidence = signal_data.get("confidence", 0)

        if confidence <= 1:
            return confidence >= self.ALERT_CONFIDENCE_THRESHOLD
        else:
            return confidence >= 4


# Singleton instance
_telegram_service: Optional[TelegramBotService] = None


def get_telegram_service() -> TelegramBotService:
    """Get or create Telegram bot service instance."""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramBotService()
    return _telegram_service
