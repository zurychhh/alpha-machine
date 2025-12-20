# ALPHA MACHINE - COMPLETE BUILD SPECIFICATION
## Technical Implementation Guide for Claude Code

**Version:** 1.0  
**Target Tier:** STARTER ($100/mo)  
**Build Time:** 2 weeks (6 milestones)  
**Automation Level:** 95% (human only for final approve/reject)

---

## 🎯 PROJECT OVERVIEW

**What we're building:**
A fully automated AI-powered stock trading intelligence system that:
- Monitors 10-20 AI stocks 24/7
- Analyzes each stock with 4 different AI agents
- Generates BUY/SELL signals via multi-agent consensus
- Tracks portfolio performance
- Requires <30 min/day human oversight

**Tech Stack:**
- **Backend:** Python 3.11+, FastAPI, PostgreSQL, Redis, Celery
- **AI/ML:** OpenAI, Anthropic, Google AI, TensorFlow
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Infrastructure:** Railway (backend), Vercel (frontend)

---

## 📁 COMPLETE PROJECT STRUCTURE

```
alpha-machine/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Settings, env vars
│   │   │   ├── database.py            # SQLAlchemy setup
│   │   │   └── security.py            # API auth (optional)
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── signal.py              # Signal model
│   │   │   ├── portfolio.py           # Portfolio model
│   │   │   ├── agent_analysis.py      # Agent analysis model
│   │   │   └── watchlist.py           # Watchlist model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── signal.py              # Pydantic schemas
│   │   │   ├── portfolio.py
│   │   │   └── agent.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py                # Dependencies
│   │   │   └── endpoints/
│   │   │       ├── __init__.py
│   │   │       ├── signals.py         # GET /signals
│   │   │       ├── portfolio.py       # GET /portfolio
│   │   │       ├── agents.py          # GET /agents/analysis
│   │   │       └── health.py          # GET /health
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── market_data.py         # Polygon, Finnhub, AV
│   │   │   ├── sentiment_data.py      # Reddit, Twitter, News
│   │   │   ├── data_aggregator.py     # Orchestrate all data
│   │   │   └── signal_generator.py    # Multi-agent consensus
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py          # Abstract agent class
│   │   │   ├── contrarian_agent.py    # GPT-4 agent
│   │   │   ├── growth_agent.py        # Claude agent
│   │   │   ├── multimodal_agent.py    # Gemini agent
│   │   │   └── predictor_agent.py     # LSTM agent
│   │   │
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── lstm_model.py          # LSTM price predictor
│   │   │   ├── train_lstm.py          # Training script
│   │   │   └── sentiment_analyzer.py  # FinBERT wrapper
│   │   │
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py          # Celery config
│   │   │   ├── data_tasks.py          # Scheduled data fetch
│   │   │   └── signal_tasks.py        # Scheduled signal gen
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py              # Logging setup
│   │       └── helpers.py             # Misc utilities
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents.py
│   │   ├── test_data.py
│   │   └── test_signals.py
│   │
│   ├── alembic/                       # DB migrations
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SignalCard.tsx
│   │   │   ├── AgentVote.tsx
│   │   │   ├── PortfolioSummary.tsx
│   │   │   ├── PerformanceChart.tsx
│   │   │   └── WatchlistTable.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # Main page
│   │   │   ├── Signals.tsx            # Signals feed
│   │   │   ├── Portfolio.tsx          # Portfolio view
│   │   │   └── Analytics.tsx          # Performance analytics
│   │   │
│   │   ├── services/
│   │   │   └── api.ts                 # Backend API client
│   │   │
│   │   ├── types/
│   │   │   └── index.ts               # TypeScript types
│   │   │
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── README.md
│
├── scripts/
│   ├── setup_db.sql                   # Initial DB schema
│   ├── seed_watchlist.py              # Seed AI stocks
│   ├── test_apis.py                   # Test API keys
│   └── backtest.py                    # Backtest signals
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🗄️ DATABASE SCHEMA

### PostgreSQL Tables

```sql
-- Watchlist: AI stocks to monitor
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(100),
    sector VARCHAR(50),
    tier INTEGER, -- 1=Core, 2=Growth, 3=Tactical
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Signals: Generated buy/sell signals
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    ticker VARCHAR(10) NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- BUY, SELL, HOLD
    confidence INTEGER NOT NULL, -- 1-5 (number of agents agreeing)
    entry_price DECIMAL(10,2),
    target_price DECIMAL(10,2),
    stop_loss DECIMAL(10,2),
    position_size INTEGER, -- Number of shares
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, APPROVED, EXECUTED, CLOSED
    executed_at TIMESTAMP,
    closed_at TIMESTAMP,
    pnl DECIMAL(10,2),
    notes TEXT,
    FOREIGN KEY (ticker) REFERENCES watchlist(ticker)
);

-- Agent Analysis: Individual agent recommendations
CREATE TABLE agent_analysis (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL,
    agent_name VARCHAR(50) NOT NULL, -- contrarian, growth, multimodal, predictor
    recommendation VARCHAR(10) NOT NULL, -- BUY, SELL, HOLD
    confidence INTEGER NOT NULL, -- 1-5
    reasoning TEXT NOT NULL, -- Why this recommendation
    data_used JSONB, -- What data was analyzed
    timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- Portfolio: Current positions
CREATE TABLE portfolio (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    shares INTEGER NOT NULL,
    avg_cost DECIMAL(10,2) NOT NULL,
    current_price DECIMAL(10,2),
    market_value DECIMAL(10,2),
    unrealized_pnl DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (ticker) REFERENCES watchlist(ticker)
);

-- Performance: Daily tracking
CREATE TABLE performance (
    id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    portfolio_value DECIMAL(12,2) NOT NULL,
    cash_balance DECIMAL(12,2),
    daily_pnl DECIMAL(10,2),
    total_pnl DECIMAL(10,2),
    num_positions INTEGER,
    win_rate DECIMAL(5,2),
    sharpe_ratio DECIMAL(5,2),
    max_drawdown DECIMAL(5,2)
);

-- Market Data Cache: Store fetched data
CREATE TABLE market_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    source VARCHAR(50), -- polygon, finnhub, alphavantage
    UNIQUE(ticker, timestamp, source)
);

-- Sentiment Data: Social/news sentiment
CREATE TABLE sentiment_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL, -- reddit, twitter, news
    sentiment_score DECIMAL(3,2), -- -1 to +1
    mention_count INTEGER,
    raw_data JSONB,
    FOREIGN KEY (ticker) REFERENCES watchlist(ticker)
);

-- Create indexes for performance
CREATE INDEX idx_signals_ticker ON signals(ticker);
CREATE INDEX idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX idx_signals_status ON signals(status);
CREATE INDEX idx_agent_analysis_signal ON agent_analysis(signal_id);
CREATE INDEX idx_market_data_ticker_time ON market_data(ticker, timestamp DESC);
CREATE INDEX idx_sentiment_ticker_time ON sentiment_data(ticker, timestamp DESC);
```

---

## ⚙️ BACKEND IMPLEMENTATION

### 1. Core Configuration (`app/core/config.py`)

```python
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Alpha Machine"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # API Keys - Market Data
    POLYGON_API_KEY: str
    FINNHUB_API_KEY: str
    ALPHA_VANTAGE_API_KEY: str
    
    # API Keys - Sentiment
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_USER_AGENT: str = "alpha-machine-bot/1.0"
    NEWS_API_KEY: str
    
    # API Keys - AI Models
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    GOOGLE_AI_API_KEY: str
    
    # Trading Parameters
    STARTING_CAPITAL: float = 50000.0
    MAX_POSITION_SIZE_PCT: float = 0.10  # 10% max per stock
    MAX_SINGLE_POSITION_PCT: float = 0.30  # 30% for NVDA exception
    MIN_CONFIDENCE_FOR_TRADE: int = 3  # 3/4 agents must agree
    STOP_LOSS_PCT: float = 0.10  # 10% stop loss
    TAKE_PROFIT_LEVELS: List[float] = [0.25, 0.50, 1.00]  # 25%, 50%, 100%
    
    # Watchlist
    WATCHLIST_TICKERS: List[str] = [
        "NVDA", "MSFT", "GOOGL", "AMD", "TSM", "AVGO",  # Tier 1
        "PLTR", "AI", "CRWD", "SNOW",  # Tier 2
    ]
    
    # Scheduling
    DATA_FETCH_INTERVAL_MINUTES: int = 5
    SIGNAL_GENERATION_INTERVAL_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

### 2. Database Setup (`app/core/database.py`)

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3. Models (`app/models/signal.py`)

```python
from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    ticker = Column(String(10), ForeignKey("watchlist.ticker"), nullable=False)
    signal_type = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Integer, nullable=False)  # 1-5
    entry_price = Column(DECIMAL(10, 2))
    target_price = Column(DECIMAL(10, 2))
    stop_loss = Column(DECIMAL(10, 2))
    position_size = Column(Integer)
    status = Column(String(20), default="PENDING")
    executed_at = Column(TIMESTAMP)
    closed_at = Column(TIMESTAMP)
    pnl = Column(DECIMAL(10, 2))
    notes = Column(Text)

class AgentAnalysis(Base):
    __tablename__ = "agent_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    agent_name = Column(String(50), nullable=False)
    recommendation = Column(String(10), nullable=False)
    confidence = Column(Integer, nullable=False)
    reasoning = Column(Text, nullable=False)
    data_used = Column(Text)  # JSON string
    timestamp = Column(TIMESTAMP, server_default=func.now())
```

### 4. Market Data Service (`app/services/market_data.py`)

```python
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MarketDataService:
    """Aggregate market data from multiple sources"""
    
    def __init__(self):
        self.polygon_base = "https://api.polygon.io"
        self.finnhub_base = "https://finnhub.io/api/v1"
        self.av_base = "https://www.alphavantage.co/query"
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """Get current price (try Polygon first, fallback to Finnhub)"""
        try:
            # Polygon (FREE tier has 5 calls/min)
            url = f"{self.polygon_base}/v2/aggs/ticker/{ticker}/prev"
            params = {"apiKey": settings.POLYGON_API_KEY}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    return data["results"][0]["c"]  # close price
        except Exception as e:
            logger.warning(f"Polygon failed for {ticker}: {e}")
        
        # Fallback to Finnhub
        try:
            url = f"{self.finnhub_base}/quote"
            params = {"symbol": ticker, "token": settings.FINNHUB_API_KEY}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("c")  # current price
        except Exception as e:
            logger.error(f"Finnhub failed for {ticker}: {e}")
            return None
    
    def get_historical_data(self, ticker: str, days: int = 30) -> List[Dict]:
        """Get historical OHLCV data"""
        try:
            # Alpha Vantage (FREE tier: 25 calls/day)
            url = self.av_base
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "apikey": settings.ALPHA_VANTAGE_API_KEY,
                "outputsize": "compact"  # last 100 days
            }
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                time_series = data.get("Time Series (Daily)", {})
                
                result = []
                for date_str, values in list(time_series.items())[:days]:
                    result.append({
                        "date": date_str,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": int(values["5. volume"])
                    })
                return result
        except Exception as e:
            logger.error(f"Historical data failed for {ticker}: {e}")
            return []
    
    def get_technical_indicators(self, ticker: str) -> Dict:
        """Get technical indicators (RSI, MACD, etc.)"""
        try:
            # Alpha Vantage technical indicators
            indicators = {}
            
            # RSI
            url = self.av_base
            params = {
                "function": "RSI",
                "symbol": ticker,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close",
                "apikey": settings.ALPHA_VANTAGE_API_KEY
            }
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                technical = data.get("Technical Analysis: RSI", {})
                if technical:
                    latest_date = list(technical.keys())[0]
                    indicators["rsi"] = float(technical[latest_date]["RSI"])
            
            return indicators
        except Exception as e:
            logger.error(f"Technical indicators failed for {ticker}: {e}")
            return {}

market_data_service = MarketDataService()
```

### 5. Sentiment Data Service (`app/services/sentiment_data.py`)

```python
import praw
import requests
from typing import Dict, List
from datetime import datetime, timedelta
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class SentimentDataService:
    """Aggregate sentiment from Reddit, Twitter, News"""
    
    def __init__(self):
        # Reddit
        self.reddit = praw.Reddit(
            client_id=settings.REDDIT_CLIENT_ID,
            client_secret=settings.REDDIT_CLIENT_SECRET,
            user_agent=settings.REDDIT_USER_AGENT
        )
    
    def get_reddit_sentiment(self, ticker: str) -> Dict:
        """Scrape Reddit mentions and sentiment"""
        try:
            mentions = 0
            positive = 0
            negative = 0
            
            # Search r/wallstreetbets and r/stocks
            for subreddit_name in ["wallstreetbets", "stocks", "investing"]:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Search last 24 hours
                for submission in subreddit.search(ticker, time_filter="day", limit=50):
                    mentions += 1
                    
                    # Simple sentiment (count upvotes as positive signal)
                    if submission.score > 10:
                        positive += 1
                    elif submission.score < -5:
                        negative += 1
            
            # Calculate sentiment score (-1 to +1)
            if mentions > 0:
                sentiment_score = (positive - negative) / mentions
            else:
                sentiment_score = 0.0
            
            return {
                "source": "reddit",
                "ticker": ticker,
                "mentions": mentions,
                "sentiment_score": sentiment_score,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Reddit sentiment failed for {ticker}: {e}")
            return {"mentions": 0, "sentiment_score": 0.0}
    
    def get_news_sentiment(self, ticker: str) -> Dict:
        """Fetch news and analyze sentiment"""
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": ticker,
                "apiKey": settings.NEWS_API_KEY,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 20
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                # Simple sentiment based on headline keywords
                positive_keywords = ["surge", "rally", "gain", "bullish", "upgrade", "beats"]
                negative_keywords = ["plunge", "drop", "bearish", "downgrade", "misses", "concern"]
                
                positive_count = 0
                negative_count = 0
                
                for article in articles:
                    title = article.get("title", "").lower()
                    for keyword in positive_keywords:
                        if keyword in title:
                            positive_count += 1
                    for keyword in negative_keywords:
                        if keyword in title:
                            negative_count += 1
                
                total = len(articles)
                sentiment_score = (positive_count - negative_count) / total if total > 0 else 0.0
                
                return {
                    "source": "news",
                    "ticker": ticker,
                    "article_count": total,
                    "sentiment_score": sentiment_score,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"News sentiment failed for {ticker}: {e}")
            return {"article_count": 0, "sentiment_score": 0.0}
    
    def aggregate_sentiment(self, ticker: str) -> Dict:
        """Combine all sentiment sources"""
        reddit_data = self.get_reddit_sentiment(ticker)
        news_data = self.get_news_sentiment(ticker)
        
        # Weighted average (Reddit 60%, News 40%)
        combined_score = (
            reddit_data["sentiment_score"] * 0.6 +
            news_data["sentiment_score"] * 0.4
        )
        
        return {
            "ticker": ticker,
            "combined_sentiment": combined_score,
            "reddit": reddit_data,
            "news": news_data,
            "timestamp": datetime.now().isoformat()
        }

sentiment_service = SentimentDataService()
```

### 6. AI Agents - Base Class (`app/agents/base_agent.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Literal

class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def analyze(self, ticker: str, market_data: Dict, sentiment_data: Dict) -> Dict:
        """
        Analyze stock and return recommendation
        
        Returns:
            {
                "recommendation": "BUY" | "SELL" | "HOLD",
                "confidence": 1-5,
                "reasoning": "Why this recommendation",
                "data_used": {...}
            }
        """
        pass
    
    def _build_recommendation(
        self,
        recommendation: Literal["BUY", "SELL", "HOLD"],
        confidence: int,
        reasoning: str,
        data_used: Dict
    ) -> Dict:
        """Helper to build standardized response"""
        return {
            "agent": self.name,
            "recommendation": recommendation,
            "confidence": max(1, min(5, confidence)),  # Clamp 1-5
            "reasoning": reasoning,
            "data_used": data_used
        }
```

### 7. Contrarian Agent - GPT-4 (`app/agents/contrarian_agent.py`)

```python
from openai import OpenAI
from app.agents.base_agent import BaseAgent
from app.core.config import settings
from typing import Dict
import json

class ContrarianAgent(BaseAgent):
    """GPT-4 powered contrarian/deep value analysis"""
    
    def __init__(self):
        super().__init__("contrarian")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def analyze(self, ticker: str, market_data: Dict, sentiment_data: Dict) -> Dict:
        """Deep value / contrarian analysis"""
        
        # Build context for GPT-4
        current_price = market_data.get("current_price", 0)
        rsi = market_data.get("indicators", {}).get("rsi", 50)
        sentiment = sentiment_data.get("combined_sentiment", 0)
        
        prompt = f"""You are a contrarian value investor analyzing {ticker}.

Current Data:
- Price: ${current_price}
- RSI: {rsi}
- Sentiment Score: {sentiment} (-1=very bearish, +1=very bullish)
- Recent sentiment mentions: {sentiment_data.get('reddit', {}).get('mentions', 0)} on Reddit

Your contrarian philosophy:
1. Buy when others are fearful (negative sentiment + oversold)
2. Sell when others are greedy (extreme positive sentiment + overbought)
3. Look for value when RSI < 30 (oversold)
4. Be cautious when RSI > 70 (overbought)

Provide your recommendation in STRICT JSON format:
{{
    "recommendation": "BUY" or "SELL" or "HOLD",
    "confidence": 1-5,
    "reasoning": "2-3 sentence explanation of your contrarian view",
    "key_factors": ["factor1", "factor2"]
}}

Respond ONLY with valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return self._build_recommendation(
                recommendation=result["recommendation"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                data_used={
                    "current_price": current_price,
                    "rsi": rsi,
                    "sentiment": sentiment
                }
            )
        except Exception as e:
            # Fallback if API fails
            return self._build_recommendation(
                recommendation="HOLD",
                confidence=1,
                reasoning=f"Analysis failed: {str(e)}",
                data_used={}
            )
```

### 8. Growth Agent - Claude (`app/agents/growth_agent.py`)

```python
from anthropic import Anthropic
from app.agents.base_agent import BaseAgent
from app.core.config import settings
from typing import Dict
import json

class GrowthAgent(BaseAgent):
    """Claude powered growth/momentum analysis"""
    
    def __init__(self):
        super().__init__("growth")
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    def analyze(self, ticker: str, market_data: Dict, sentiment_data: Dict) -> Dict:
        """Risk-adjusted growth analysis"""
        
        current_price = market_data.get("current_price", 0)
        historical = market_data.get("historical", [])
        
        # Calculate simple momentum (30-day price change)
        if len(historical) >= 30:
            price_30d_ago = historical[29]["close"]
            momentum_pct = ((current_price - price_30d_ago) / price_30d_ago) * 100
        else:
            momentum_pct = 0
        
        sentiment = sentiment_data.get("combined_sentiment", 0)
        
        prompt = f"""You are a growth investor focused on momentum and risk-adjusted returns for {ticker}.

Current Data:
- Current Price: ${current_price}
- 30-day Momentum: {momentum_pct:.2f}%
- Sentiment: {sentiment:.2f} (-1 to +1)
- Volume Trend: {market_data.get('volume_trend', 'neutral')}

Your growth philosophy:
1. Buy strong momentum stocks (>10% monthly gain) with positive sentiment
2. Avoid stocks with negative momentum (<-5%) 
3. Risk management: Never buy overbought stocks without confirmation
4. Prefer stocks with increasing volume + positive sentiment

Provide STRICT JSON response:
{{
    "recommendation": "BUY" or "SELL" or "HOLD",
    "confidence": 1-5,
    "reasoning": "2-3 sentence growth thesis",
    "risk_factors": ["factor1", "factor2"]
}}

JSON only, no other text."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=300,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(message.content[0].text)
            
            return self._build_recommendation(
                recommendation=result["recommendation"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                data_used={
                    "current_price": current_price,
                    "momentum_30d": momentum_pct,
                    "sentiment": sentiment
                }
            )
        except Exception as e:
            return self._build_recommendation(
                recommendation="HOLD",
                confidence=1,
                reasoning=f"Analysis failed: {str(e)}",
                data_used={}
            )
```

### 9. Signal Generator (`app/services/signal_generator.py`)

```python
from typing import List, Dict
from app.agents.contrarian_agent import ContrarianAgent
from app.agents.growth_agent import GrowthAgent
# Import other agents...
from app.services.market_data import market_data_service
from app.services.sentiment_data import sentiment_service
from app.models.signal import Signal, AgentAnalysis
from sqlalchemy.orm import Session
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SignalGenerator:
    """Multi-agent consensus signal generation"""
    
    def __init__(self):
        self.agents = [
            ContrarianAgent(),
            GrowthAgent(),
            # MultiModalAgent(),  # Add when implemented
            # PredictorAgent(),   # Add when implemented
        ]
    
    def generate_signal(self, ticker: str, db: Session) -> Signal:
        """
        Analyze ticker with all agents and generate consensus signal
        
        Process:
        1. Fetch market data + sentiment
        2. Each agent analyzes independently
        3. Calculate consensus (majority vote)
        4. Generate signal with confidence score
        5. Save to database
        """
        
        # Step 1: Gather data
        logger.info(f"Generating signal for {ticker}")
        
        current_price = market_data_service.get_current_price(ticker)
        historical_data = market_data_service.get_historical_data(ticker, days=30)
        technical_indicators = market_data_service.get_technical_indicators(ticker)
        sentiment_data = sentiment_service.aggregate_sentiment(ticker)
        
        market_data = {
            "current_price": current_price,
            "historical": historical_data,
            "indicators": technical_indicators
        }
        
        # Step 2: Get agent recommendations
        agent_results = []
        for agent in self.agents:
            try:
                result = agent.analyze(ticker, market_data, sentiment_data)
                agent_results.append(result)
                logger.info(f"{agent.name}: {result['recommendation']} (confidence: {result['confidence']})")
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
        
        # Step 3: Calculate consensus
        buy_votes = sum(1 for r in agent_results if r["recommendation"] == "BUY")
        sell_votes = sum(1 for r in agent_results if r["recommendation"] == "SELL")
        hold_votes = sum(1 for r in agent_results if r["recommendation"] == "HOLD")
        
        total_agents = len(agent_results)
        
        # Determine signal type
        if buy_votes >= total_agents * 0.75:  # 75%+ agree BUY
            signal_type = "BUY"
            confidence = 5
        elif buy_votes >= total_agents * 0.5:  # 50%+ agree BUY
            signal_type = "BUY"
            confidence = 4
        elif sell_votes >= total_agents * 0.75:
            signal_type = "SELL"
            confidence = 5
        elif sell_votes >= total_agents * 0.5:
            signal_type = "SELL"
            confidence = 4
        else:
            signal_type = "HOLD"
            confidence = buy_votes + sell_votes  # Mixed signals = low confidence
        
        # Step 4: Calculate position sizing and risk params
        if signal_type == "BUY":
            stop_loss = current_price * 0.90  # 10% stop loss
            target_price = current_price * 1.25  # 25% target
            position_size = self._calculate_position_size(current_price, confidence)
        else:
            stop_loss = None
            target_price = None
            position_size = 0
        
        # Step 5: Create signal in DB
        signal = Signal(
            ticker=ticker,
            signal_type=signal_type,
            confidence=confidence,
            entry_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=position_size,
            status="PENDING"
        )
        
        db.add(signal)
        db.commit()
        db.refresh(signal)
        
        # Save agent analyses
        for result in agent_results:
            analysis = AgentAnalysis(
                signal_id=signal.id,
                agent_name=result["agent"],
                recommendation=result["recommendation"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                data_used=str(result.get("data_used", {}))
            )
            db.add(analysis)
        
        db.commit()
        
        logger.info(f"Signal generated: {signal_type} {ticker} @ ${current_price} (confidence: {confidence})")
        return signal
    
    def _calculate_position_size(self, price: float, confidence: int) -> int:
        """Calculate number of shares based on confidence"""
        from app.core.config import settings
        
        # Max position value = 10% of capital
        max_position_value = settings.STARTING_CAPITAL * settings.MAX_POSITION_SIZE_PCT
        
        # Scale by confidence (1-5)
        confidence_multiplier = confidence / 5.0
        position_value = max_position_value * confidence_multiplier
        
        # Calculate shares
        shares = int(position_value / price)
        return shares

signal_generator = SignalGenerator()
```

---

## 🎨 FRONTEND IMPLEMENTATION

### 1. API Client (`frontend/src/services/api.ts`)

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface Signal {
  id: number;
  ticker: string;
  signal_type: 'BUY' | 'SELL' | 'HOLD';
  confidence: number;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  position_size: number;
  status: string;
  timestamp: string;
}

export interface AgentAnalysis {
  agent_name: string;
  recommendation: string;
  confidence: number;
  reasoning: string;
}

export const api = {
  // Get today's signals
  async getSignals(): Promise<Signal[]> {
    const response = await fetch(`${API_BASE}/signals`);
    return response.json();
  },
  
  // Get signal details with agent reasoning
  async getSignalDetails(signalId: number): Promise<{
    signal: Signal;
    agent_analyses: AgentAnalysis[];
  }> {
    const response = await fetch(`${API_BASE}/signals/${signalId}`);
    return response.json();
  },
  
  // Get portfolio
  async getPortfolio() {
    const response = await fetch(`${API_BASE}/portfolio`);
    return response.json();
  },
  
  // Approve signal (manual)
  async approveSignal(signalId: number) {
    const response = await fetch(`${API_BASE}/signals/${signalId}/approve`, {
      method: 'POST'
    });
    return response.json();
  }
};
```

### 2. Dashboard Component (`frontend/src/pages/Dashboard.tsx`)

```typescript
import { useEffect, useState } from 'react';
import { api, Signal } from '../services/api';
import SignalCard from '../components/SignalCard';

export default function Dashboard() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadSignals();
    // Refresh every 5 minutes
    const interval = setInterval(loadSignals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);
  
  async function loadSignals() {
    try {
      const data = await api.getSignals();
      setSignals(data);
    } catch (error) {
      console.error('Failed to load signals:', error);
    } finally {
      setLoading(false);
    }
  }
  
  const strongBuySignals = signals.filter(s => 
    s.signal_type === 'BUY' && s.confidence >= 4
  );
  
  const weakSignals = signals.filter(s => 
    s.confidence < 4
  );
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Alpha Machine Dashboard</h1>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">
          🔥 Strong Signals ({strongBuySignals.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {strongBuySignals.map(signal => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      </div>
      
      <div>
        <h2 className="text-xl font-semibold mb-4">
          📊 Weak Signals ({weakSignals.length})
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {weakSignals.map(signal => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## 📦 DEPENDENCIES

### Backend (`requirements.txt`)

```txt
# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Redis & Celery
redis==5.0.1
celery==5.3.6

# API Clients
requests==2.31.0
httpx==0.26.0

# AI/ML
openai==1.10.0
anthropic==0.18.0
google-generativeai==0.3.2
tensorflow==2.15.0
transformers==4.37.0

# Data & Sentiment
praw==7.7.1
beautifulsoup4==4.12.3
pandas==2.1.4
numpy==1.26.3

# Utilities
python-dotenv==1.0.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

### Frontend (`package.json`)

```json
{
  "name": "alpha-machine-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.1",
    "recharts": "^2.10.3"
  },
  "devDependencies": {
    "@types/react": "^18.2.47",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.33"
  }
}
```

---

## 🚀 DEPLOYMENT

### Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: alphamachine
      POSTGRES_USER: alpha
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://alpha:${DB_PASSWORD}@postgres:5432/alphamachine
      REDIS_URL: redis://redis:6379
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
  
  celery_worker:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://alpha:${DB_PASSWORD}@postgres:5432/alphamachine
      REDIS_URL: redis://redis:6379
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.tasks.celery_app worker --loglevel=info
  
  celery_beat:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://alpha:${DB_PASSWORD}@postgres:5432/alphamachine
      REDIS_URL: redis://redis:6379
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    command: celery -A app.tasks.celery_app beat --loglevel=info

volumes:
  postgres_data:
```

---

## ✅ TESTING & VALIDATION

### API Key Test Script (`scripts/test_apis.py`)

```python
"""Test all API keys before starting"""
import os
from dotenv import load_dotenv
import requests

load_dotenv()

def test_polygon():
    key = os.getenv("POLYGON_API_KEY")
    url = f"https://api.polygon.io/v2/aggs/ticker/AAPL/prev?apiKey={key}"
    response = requests.get(url)
    return response.status_code == 200

def test_openai():
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        return True
    except:
        return False

# Run all tests
tests = {
    "Polygon.io": test_polygon,
    "OpenAI": test_openai,
    # Add more...
}

print("Testing API keys...")
for name, test_fn in tests.items():
    result = "✅ PASS" if test_fn() else "❌ FAIL"
    print(f"{name}: {result}")
```

---

## 📊 SUCCESS CRITERIA

**Milestone 1 Complete when:**
- ✅ All files created, no syntax errors
- ✅ Docker compose starts successfully
- ✅ Database schema created
- ✅ API health endpoint returns 200

**Milestone 2 Complete when:**
- ✅ Market data fetch works for NVDA
- ✅ Sentiment data returns from Reddit
- ✅ Data stored in PostgreSQL

**Milestone 3 Complete when:**
- ✅ GPT-4 agent returns BUY/SELL/HOLD
- ✅ Claude agent returns recommendation
- ✅ Consensus algorithm produces signal

**Milestone 4 Complete when:**
- ✅ Signal generated for test ticker
- ✅ Stored in database with confidence
- ✅ Position sizing calculated

**Milestone 5 Complete when:**
- ✅ Dashboard loads and displays signals
- ✅ Agent reasoning visible
- ✅ Real-time updates work

**Milestone 6 Complete when:**
- ✅ Paper trading logs trades
- ✅ Performance tracking works
- ✅ Deployed to Railway/Vercel

---

**END OF BUILD SPECIFICATION**

*This document contains everything Claude Code needs to build the complete STARTER tier system.*
