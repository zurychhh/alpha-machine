"""
Telegram Webhook Endpoint
Handles incoming updates from Telegram Bot API.
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

from app.services.telegram_bot import get_telegram_service
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Handle incoming Telegram webhook updates.

    This endpoint receives updates from Telegram when users
    interact with the bot (commands, messages, etc.).
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured",
        )

    try:
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data.get('update_id')}")

        # Process webhook directly (not in background)
        telegram_service = get_telegram_service()
        result = await telegram_service.process_webhook(update_data)

        return {"ok": True, "result": result}

    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process update",
        )


@router.post("/send-alert")
async def send_signal_alert(request: Request):
    """
    Manually send a signal alert to Telegram.

    Request body:
    {
        "ticker": "NVDA",
        "signal_type": "BUY",
        "confidence": 0.85,
        "entry_price": 875.50,
        "target_price": 1094.38,
        "stop_loss": 787.95
    }
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured",
        )

    try:
        signal_data = await request.json()

        telegram_service = get_telegram_service()
        success = await telegram_service.send_signal_alert(signal_data)

        if success:
            return {"status": "sent", "ticker": signal_data.get("ticker")}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send alert",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending signal alert: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.post("/send-summary")
async def send_daily_summary(request: Request):
    """
    Manually trigger daily summary.

    Request body:
    {
        "signals": [
            {"ticker": "NVDA", "signal_type": "BUY", "confidence": 0.85},
            {"ticker": "AAPL", "signal_type": "HOLD", "confidence": 0.72}
        ]
    }
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured",
        )

    try:
        data = await request.json()
        signals = data.get("signals", [])

        telegram_service = get_telegram_service()
        success = await telegram_service.send_daily_summary(signals)

        if success:
            return {"status": "sent", "signal_count": len(signals)}
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send summary",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@router.get("/status")
async def telegram_status():
    """Check Telegram bot configuration status."""
    configured = bool(settings.TELEGRAM_BOT_TOKEN)
    chat_configured = bool(settings.TELEGRAM_CHAT_ID)

    return {
        "bot_configured": configured,
        "chat_configured": chat_configured,
        "webhook_url": f"{settings.API_V1_STR}/telegram/webhook" if configured else None,
        "status": "ready" if configured and chat_configured else "not_configured",
    }


@router.post("/setup-webhook")
async def setup_webhook():
    """
    Set up Telegram webhook to point to this server.

    Call this once after deployment to register the webhook URL with Telegram.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Telegram bot not configured",
        )

    import httpx

    # Use the Railway backend URL
    webhook_url = "https://backend-production-a7f4.up.railway.app/api/v1/telegram/webhook"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
                json={"url": webhook_url},
            )
            result = response.json()

            if result.get("ok"):
                logger.info(f"Webhook set to: {webhook_url}")
                return {
                    "status": "success",
                    "webhook_url": webhook_url,
                    "telegram_response": result,
                }
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Telegram API error: {result.get('description')}",
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
