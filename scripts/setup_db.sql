-- Alpha Machine Database Schema
-- Run this script to initialize all tables

-- Watchlist: AI stocks to monitor
CREATE TABLE IF NOT EXISTS watchlist (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(100),
    sector VARCHAR(50),
    tier INTEGER, -- 1=Core, 2=Growth, 3=Tactical
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Signals: Generated buy/sell signals
CREATE TABLE IF NOT EXISTS signals (
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
CREATE TABLE IF NOT EXISTS agent_analysis (
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
CREATE TABLE IF NOT EXISTS portfolio (
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
CREATE TABLE IF NOT EXISTS performance (
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
CREATE TABLE IF NOT EXISTS market_data (
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
CREATE TABLE IF NOT EXISTS sentiment_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL, -- reddit, twitter, news
    sentiment_score DECIMAL(3,2), -- -1 to +1
    mention_count INTEGER,
    raw_data JSONB,
    FOREIGN KEY (ticker) REFERENCES watchlist(ticker)
);

-- Backtest Results: Individual trade results from backtesting
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    backtest_id VARCHAR(50) NOT NULL, -- UUID per backtest run
    signal_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    exit_price DECIMAL(10,2) NOT NULL,
    shares INTEGER NOT NULL,
    pnl DECIMAL(10,2) NOT NULL, -- Dollar P&L
    pnl_pct DECIMAL(7,3) NOT NULL, -- Percentage return
    trade_result VARCHAR(10) NOT NULL, -- WIN or LOSS
    days_held INTEGER NOT NULL,
    exit_reason VARCHAR(20), -- STOP_LOSS, TAKE_PROFIT, HOLD_PERIOD_END
    position_type VARCHAR(20), -- CORE, SATELLITE, EQUAL
    allocation_pct DECIMAL(5,3), -- e.g., 0.60 = 60%
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
CREATE INDEX IF NOT EXISTS idx_agent_analysis_signal ON agent_analysis(signal_id);
CREATE INDEX IF NOT EXISTS idx_market_data_ticker_time ON market_data(ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sentiment_ticker_time ON sentiment_data(ticker, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_backtest_results_backtest_id ON backtest_results(backtest_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_signal_id ON backtest_results(signal_id);

-- Seed initial watchlist with AI stocks
INSERT INTO watchlist (ticker, company_name, sector, tier) VALUES
    ('NVDA', 'NVIDIA Corporation', 'Semiconductors', 1),
    ('MSFT', 'Microsoft Corporation', 'Software', 1),
    ('GOOGL', 'Alphabet Inc.', 'Internet', 1),
    ('AMD', 'Advanced Micro Devices', 'Semiconductors', 1),
    ('TSM', 'Taiwan Semiconductor', 'Semiconductors', 1),
    ('AVGO', 'Broadcom Inc.', 'Semiconductors', 1),
    ('PLTR', 'Palantir Technologies', 'Software', 2),
    ('AI', 'C3.ai Inc.', 'Software', 2),
    ('CRWD', 'CrowdStrike Holdings', 'Cybersecurity', 2),
    ('SNOW', 'Snowflake Inc.', 'Cloud Computing', 2)
ON CONFLICT (ticker) DO NOTHING;
