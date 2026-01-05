"""
Telegram Bot Service - Notifications for Alpha Machine
Handles signal alerts, daily summaries, and user commands.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import asyncio

from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

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
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.logger = logging.getLogger("telegram_bot")

        if self.token:
            self.bot = Bot(token=self.token)
        else:
            self.logger.warning("TELEGRAM_BOT_TOKEN not configured")

    async def initialize(self) -> None:
        """Initialize the bot application with command handlers."""
        if not self.token:
            self.logger.error("Cannot initialize: TELEGRAM_BOT_TOKEN not set")
            return

        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )

        # Register command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("signals", self._handle_signals))
        self.application.add_handler(CommandHandler("watchlist", self._handle_watchlist))
        self.application.add_handler(CommandHandler("status", self._handle_status))
        self.application.add_handler(CommandHandler("help", self._handle_help))

        self.logger.info("Telegram bot initialized with command handlers")

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = ParseMode.HTML,
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
        if not self.bot:
            self.logger.error("Bot not initialized")
            return False

        target_chat = chat_id or self.chat_id
        if not target_chat:
            self.logger.error("No chat_id configured")
            return False

        try:
            await self.bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode=parse_mode,
            )
            self.logger.info(f"Message sent to chat {target_chat}")
            return True
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
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_message(text, chat_id))

    async def send_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """
        Send real-time alert for a high-confidence signal.

        Args:
            signal_data: Signal dictionary with ticker, signal_type, confidence, etc.

        Returns:
            True if alert sent successfully
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
        stars = self.CONFIDENCE_STARS.get(confidence if confidence > 1 else int(confidence * 5), "")

        message = f"""
🚨 <b>ALPHA MACHINE SIGNAL ALERT</b> 🚨

{emoji} <b>{ticker}</b> - <b>{signal_type}</b>

📊 <b>Confidence:</b> {conf_percent:.1f}% {stars}
💰 <b>Entry Price:</b> ${entry_price:.2f if entry_price else 'N/A'}
🎯 <b>Target:</b> ${target_price:.2f if target_price else 'N/A'}
🛑 <b>Stop Loss:</b> ${stop_loss:.2f if stop_loss else 'N/A'}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}

<i>This signal met the ≥75% confidence threshold</i>
"""

        return await self.send_message(message.strip())

    def send_signal_alert_sync(self, signal_data: Dict[str, Any]) -> bool:
        """Synchronous wrapper for send_signal_alert."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_signal_alert(signal_data))

    async def send_daily_summary(self, signals: List[Dict[str, Any]]) -> bool:
        """
        Send daily signal summary.

        Args:
            signals: List of signal dictionaries from today

        Returns:
            True if summary sent successfully
        """
        if not signals:
            message = """
📊 <b>ALPHA MACHINE DAILY SUMMARY</b>

No signals generated today.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}
"""
            return await self.send_message(message.strip())

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

        signal_list = "\n".join(signal_lines[:15])  # Limit to 15 signals

        message = f"""
📊 <b>ALPHA MACHINE DAILY SUMMARY</b>

📈 <b>Today's Signals:</b>
{signal_list}

📊 <b>Summary:</b>
  🟢 BUY: {len(buy_signals)}
  🔴 SELL: {len(sell_signals)}
  🟡 HOLD: {len(hold_signals)}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}
"""

        return await self.send_message(message.strip())

    def send_daily_summary_sync(self, signals: List[Dict[str, Any]]) -> bool:
        """Synchronous wrapper for send_daily_summary."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.send_daily_summary(signals))

    # Command Handlers

    async def _handle_start(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /start command."""
        chat_id = update.effective_chat.id
        message = f"""
🤖 <b>Welcome to Alpha Machine Bot!</b>

Your AI-powered stock trading assistant.

<b>Your Chat ID:</b> <code>{chat_id}</code>
(Add this to TELEGRAM_CHAT_ID in your environment)

<b>Available Commands:</b>
/signals - View recent trading signals
/watchlist - View monitored stocks
/status - Check system status
/help - Show this help message

<i>You'll receive real-time alerts for signals with ≥75% confidence.</i>
"""
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    async def _handle_signals(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /signals command - show recent signals."""
        # Import here to avoid circular imports
        from app.core.database import get_db
        from app.services.signal_service import SignalService

        try:
            db = next(get_db())
            service = SignalService(db)
            signals = service.get_signals(days=1, limit=10)

            if not signals:
                await update.message.reply_text(
                    "📊 No signals in the last 24 hours.",
                    parse_mode=ParseMode.HTML,
                )
                return

            lines = ["📊 <b>Recent Signals (Last 24h):</b>\n"]
            for signal in signals:
                emoji = self.SIGNAL_EMOJIS.get(signal.signal_type, "⚪")
                conf_percent = signal.confidence * 20  # 1-5 to percentage
                lines.append(
                    f"  {emoji} <b>{signal.ticker}</b>: {signal.signal_type} "
                    f"({conf_percent:.0f}%) @ ${float(signal.entry_price):.2f}"
                )

            await update.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            self.logger.error(f"Error in /signals: {e}")
            await update.message.reply_text(
                "❌ Error fetching signals. Please try again.",
            )

    async def _handle_watchlist(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /watchlist command - show monitored stocks."""
        from app.core.database import get_db
        from app.models.watchlist import Watchlist

        try:
            db = next(get_db())
            stocks = db.query(Watchlist).filter(Watchlist.active == True).all()

            if not stocks:
                await update.message.reply_text(
                    "📋 Watchlist is empty.",
                    parse_mode=ParseMode.HTML,
                )
                return

            lines = ["📋 <b>Watchlist:</b>\n"]
            for stock in stocks:
                tier_emoji = "⭐" if stock.priority <= 2 else ""
                lines.append(f"  • <b>{stock.ticker}</b> {tier_emoji}")

            lines.append(f"\n<i>Total: {len(stocks)} stocks</i>")

            await update.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.HTML,
            )
        except Exception as e:
            self.logger.error(f"Error in /watchlist: {e}")
            await update.message.reply_text(
                "❌ Error fetching watchlist. Please try again.",
            )

    async def _handle_status(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /status command - show system status."""
        from app.core.database import get_db
        from app.models.signal import Signal
        from app.models.watchlist import Watchlist

        try:
            db = next(get_db())

            # Count signals
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())

            total_signals = db.query(Signal).count()
            today_signals = (
                db.query(Signal)
                .filter(Signal.timestamp >= today_start)
                .count()
            )

            # Count active stocks
            active_stocks = (
                db.query(Watchlist)
                .filter(Watchlist.active == True)
                .count()
            )

            message = f"""
🖥️ <b>Alpha Machine Status</b>

✅ <b>System:</b> Online
📊 <b>Total Signals:</b> {total_signals}
📈 <b>Today's Signals:</b> {today_signals}
📋 <b>Active Stocks:</b> {active_stocks}

🤖 <b>AI Agents:</b>
  • ContrarianAgent (GPT-4o) ✅
  • GrowthAgent (Claude) ✅
  • MultiModalAgent (Gemini) ✅
  • PredictorAgent (Local) ✅

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M EST')}
"""

            await update.message.reply_text(message, parse_mode=ParseMode.HTML)
        except Exception as e:
            self.logger.error(f"Error in /status: {e}")
            await update.message.reply_text(
                "❌ Error fetching status. Please try again.",
            )

    async def _handle_help(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle /help command."""
        message = """
🤖 <b>Alpha Machine Bot - Help</b>

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

<i>For support, visit the Alpha Machine dashboard.</i>
"""
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    async def process_webhook(self, update_data: Dict[str, Any]) -> None:
        """
        Process incoming webhook update from Telegram.

        Args:
            update_data: Raw update data from Telegram webhook
        """
        if not self.application:
            await self.initialize()

        if self.application:
            update = Update.de_json(update_data, self.bot)
            await self.application.process_update(update)

    def should_alert(self, signal_data: Dict[str, Any]) -> bool:
        """
        Check if a signal should trigger a real-time alert.

        Args:
            signal_data: Signal dictionary

        Returns:
            True if signal confidence >= 75%
        """
        confidence = signal_data.get("confidence", 0)

        # Handle both 0-1 scale and 1-5 scale
        if confidence <= 1:
            return confidence >= self.ALERT_CONFIDENCE_THRESHOLD
        else:
            # 1-5 scale: 4+ is 75%+
            return confidence >= 4


# Singleton instance
_telegram_service: Optional[TelegramBotService] = None


def get_telegram_service() -> TelegramBotService:
    """Get or create Telegram bot service instance."""
    global _telegram_service
    if _telegram_service is None:
        _telegram_service = TelegramBotService()
    return _telegram_service
