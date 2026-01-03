"""
Pytest Configuration and Fixtures
Shared test fixtures for Alpha Machine
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


# ============================================================
# MOCK API RESPONSES
# ============================================================


@pytest.fixture
def mock_polygon_success_response():
    """Mock successful Polygon.io API response"""
    return {
        "status": "OK",
        "results": [
            {
                "c": 875.50,  # close
                "h": 880.00,  # high
                "l": 870.00,  # low
                "o": 872.00,  # open
                "v": 15000000,  # volume
                "t": 1703116800000,  # timestamp
            }
        ],
    }


@pytest.fixture
def mock_polygon_historical_response():
    """Mock Polygon historical data response"""
    return {
        "status": "OK",
        "results": [
            {"c": 875.50, "h": 880.00, "l": 870.00, "o": 872.00, "v": 15000000, "t": 1703116800000},
            {"c": 870.25, "h": 878.00, "l": 868.00, "o": 875.00, "v": 14500000, "t": 1703030400000},
            {"c": 865.00, "h": 872.00, "l": 862.00, "o": 868.00, "v": 13800000, "t": 1702944000000},
        ],
    }


@pytest.fixture
def mock_finnhub_success_response():
    """Mock successful Finnhub API response"""
    return {
        "c": 875.50,  # current price
        "d": 5.25,  # change
        "dp": 0.60,  # percent change
        "h": 880.00,  # high
        "l": 870.00,  # low
        "o": 872.00,  # open
        "pc": 870.25,  # previous close
        "t": 1703116800,  # timestamp
    }


@pytest.fixture
def mock_alphavantage_daily_response():
    """Mock Alpha Vantage TIME_SERIES_DAILY response"""
    return {
        "Meta Data": {"1. Information": "Daily Prices", "2. Symbol": "NVDA"},
        "Time Series (Daily)": {
            "2024-12-20": {
                "1. open": "872.00",
                "2. high": "880.00",
                "3. low": "870.00",
                "4. close": "875.50",
                "5. volume": "15000000",
            },
            "2024-12-19": {
                "1. open": "875.00",
                "2. high": "878.00",
                "3. low": "868.00",
                "4. close": "870.25",
                "5. volume": "14500000",
            },
            "2024-12-18": {
                "1. open": "868.00",
                "2. high": "872.00",
                "3. low": "862.00",
                "4. close": "865.00",
                "5. volume": "13800000",
            },
        },
    }


@pytest.fixture
def mock_alphavantage_rsi_response():
    """Mock Alpha Vantage RSI response"""
    return {
        "Meta Data": {"1: Symbol": "NVDA", "2: Indicator": "Relative Strength Index (RSI)"},
        "Technical Analysis: RSI": {
            "2024-12-20": {"RSI": "55.50"},
            "2024-12-19": {"RSI": "52.30"},
            "2024-12-18": {"RSI": "48.75"},
        },
    }


@pytest.fixture
def mock_alphavantage_rate_limit_response():
    """Mock Alpha Vantage rate limit response"""
    return {
        "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 25 calls per day."
    }


@pytest.fixture
def mock_newsapi_success_response():
    """Mock successful NewsAPI response"""
    return {
        "status": "ok",
        "totalResults": 3,
        "articles": [
            {
                "title": "NVIDIA stock surges on strong AI demand",
                "source": {"name": "Reuters"},
                "publishedAt": "2024-12-20T10:00:00Z",
                "description": "NVIDIA sees record growth...",
            },
            {
                "title": "Tech stocks rally as market gains",
                "source": {"name": "Bloomberg"},
                "publishedAt": "2024-12-20T09:00:00Z",
                "description": "Market overview...",
            },
            {
                "title": "NVDA earnings beat expectations",
                "source": {"name": "CNBC"},
                "publishedAt": "2024-12-19T15:00:00Z",
                "description": "Quarterly results...",
            },
        ],
    }


@pytest.fixture
def mock_newsapi_empty_response():
    """Mock empty NewsAPI response"""
    return {"status": "ok", "totalResults": 0, "articles": []}


# ============================================================
# REDDIT MOCK FIXTURES
# ============================================================


@pytest.fixture
def mock_reddit_submission():
    """Create mock Reddit submission"""
    submission = Mock()
    submission.title = "NVDA to the moon! Strong buy signal"
    submission.score = 150
    submission.upvote_ratio = 0.85
    submission.num_comments = 45
    submission.created_utc = datetime.now().timestamp()
    return submission


@pytest.fixture
def mock_reddit_submissions():
    """Create list of mock Reddit submissions with mixed sentiment"""
    submissions = []

    # Positive post
    pos = Mock()
    pos.title = "NVDA earnings beat, bullish outlook"
    pos.score = 200
    pos.upvote_ratio = 0.90
    submissions.append(pos)

    # Negative post
    neg = Mock()
    neg.title = "NVDA overvalued, bearish puts incoming"
    neg.score = 75
    neg.upvote_ratio = 0.65
    submissions.append(neg)

    # Neutral post
    neutral = Mock()
    neutral.title = "NVDA analysis: what do you think?"
    neutral.score = 50
    neutral.upvote_ratio = 0.70
    submissions.append(neutral)

    return submissions


# ============================================================
# MARKET DATA FIXTURES
# ============================================================


@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    return {
        "ticker": "NVDA",
        "current_price": 875.50,
        "quote": {
            "ticker": "NVDA",
            "current_price": 875.50,
            "change_percent": 0.60,
            "high": 880.00,
            "low": 870.00,
            "open": 872.00,
            "previous_close": 870.25,
        },
        "indicators": {
            "rsi": 55.50,
            "price_change_1d": 0.60,
            "price_change_7d": 3.25,
            "price_change_30d": 8.50,
            "volume_trend": "increasing",
        },
    }


@pytest.fixture
def sample_historical_data():
    """Sample historical data for testing"""
    return [
        {
            "date": "2024-12-20",
            "open": 872.00,
            "high": 880.00,
            "low": 870.00,
            "close": 875.50,
            "volume": 15000000,
            "source": "polygon",
        },
        {
            "date": "2024-12-19",
            "open": 875.00,
            "high": 878.00,
            "low": 868.00,
            "close": 870.25,
            "volume": 14500000,
            "source": "polygon",
        },
        {
            "date": "2024-12-18",
            "open": 868.00,
            "high": 872.00,
            "low": 862.00,
            "close": 865.00,
            "volume": 13800000,
            "source": "polygon",
        },
    ]


# ============================================================
# SENTIMENT DATA FIXTURES
# ============================================================


@pytest.fixture
def sample_sentiment_data():
    """Sample sentiment data for testing"""
    return {
        "ticker": "NVDA",
        "combined_sentiment": 0.45,
        "sentiment_label": "slightly_bullish",
        "reddit": {
            "source": "reddit",
            "ticker": "NVDA",
            "mentions": 25,
            "sentiment_score": 0.52,
            "positive_count": 15,
            "negative_count": 5,
            "neutral_count": 5,
        },
        "news": {
            "source": "news",
            "ticker": "NVDA",
            "article_count": 10,
            "sentiment_score": 0.35,
            "positive_count": 5,
            "negative_count": 2,
            "neutral_count": 3,
        },
        "total_mentions": 35,
    }


@pytest.fixture
def sample_bearish_sentiment():
    """Sample bearish sentiment for testing"""
    return {
        "ticker": "NVDA",
        "combined_sentiment": -0.45,
        "sentiment_label": "bearish",
        "reddit": {"mentions": 20, "sentiment_score": -0.50},
        "news": {"article_count": 8, "sentiment_score": -0.35},
    }


# ============================================================
# DATABASE FIXTURES (Mock)
# ============================================================


@pytest.fixture
def mock_db_session():
    """Mock database session"""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.query = MagicMock()
    return session


# ============================================================
# SETTINGS FIXTURES
# ============================================================


@pytest.fixture
def mock_settings_with_keys():
    """Mock settings with API keys configured"""
    settings = Mock()
    settings.POLYGON_API_KEY = "test_polygon_key"
    settings.FINNHUB_API_KEY = "test_finnhub_key"
    settings.ALPHA_VANTAGE_API_KEY = "test_av_key"
    settings.NEWS_API_KEY = "test_news_key"
    settings.REDDIT_CLIENT_ID = "test_reddit_id"
    settings.REDDIT_CLIENT_SECRET = "test_reddit_secret"
    settings.REDDIT_USER_AGENT = "TestAgent/1.0"
    settings.STARTING_CAPITAL = 50000.0
    settings.MAX_POSITION_SIZE_PCT = 0.10
    return settings


@pytest.fixture
def mock_settings_no_keys():
    """Mock settings without API keys"""
    settings = Mock()
    settings.POLYGON_API_KEY = None
    settings.FINNHUB_API_KEY = None
    settings.ALPHA_VANTAGE_API_KEY = None
    settings.NEWS_API_KEY = None
    settings.REDDIT_CLIENT_ID = None
    settings.REDDIT_CLIENT_SECRET = None
    return settings
