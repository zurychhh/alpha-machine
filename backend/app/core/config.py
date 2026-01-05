from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Alpha Machine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://alpha:alphapass@localhost:5432/alphamachine"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # API Keys - Market Data
    POLYGON_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    ALPHA_VANTAGE_API_KEY: str = ""

    # API Keys - Sentiment
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "alpha-machine-bot/1.0"
    NEWS_API_KEY: str = ""

    # API Keys - AI Models
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_AI_API_KEY: str = ""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    # Trading Parameters
    STARTING_CAPITAL: float = 50000.0
    MAX_POSITION_SIZE_PCT: float = 0.10  # 10% max per stock
    MAX_SINGLE_POSITION_PCT: float = 0.30  # 30% for NVDA exception
    MIN_CONFIDENCE_FOR_TRADE: int = 3  # 3/4 agents must agree
    STOP_LOSS_PCT: float = 0.10  # 10% stop loss
    TAKE_PROFIT_LEVELS: List[float] = [0.25, 0.50, 1.00]  # 25%, 50%, 100%

    # Watchlist
    WATCHLIST_TICKERS: List[str] = [
        "NVDA",
        "MSFT",
        "GOOGL",
        "AMD",
        "TSM",
        "AVGO",  # Tier 1
        "PLTR",
        "AI",
        "CRWD",
        "SNOW",  # Tier 2
    ]

    # Scheduling
    DATA_FETCH_INTERVAL_MINUTES: int = 5
    SIGNAL_GENERATION_INTERVAL_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
