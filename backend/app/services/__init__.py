"""
Services Layer
Data fetching, aggregation, and backtesting services
"""

from app.services.market_data import market_data_service, MarketDataService
from app.services.sentiment_data import sentiment_service, SentimentDataService
from app.services.data_aggregator import data_aggregator, DataAggregatorService
from app.services.signal_service import SignalService, get_signal_service
from app.services.signal_ranker import signal_ranker, SignalRanker
from app.services.portfolio_allocator import portfolio_allocator, PortfolioAllocator
from app.services.backtesting import backtest_engine, BacktestEngine
from app.services.telegram_bot import TelegramBotService, get_telegram_service

__all__ = [
    "market_data_service",
    "MarketDataService",
    "sentiment_service",
    "SentimentDataService",
    "data_aggregator",
    "DataAggregatorService",
    "SignalService",
    "get_signal_service",
    "signal_ranker",
    "SignalRanker",
    "portfolio_allocator",
    "PortfolioAllocator",
    "backtest_engine",
    "BacktestEngine",
    "TelegramBotService",
    "get_telegram_service",
]
