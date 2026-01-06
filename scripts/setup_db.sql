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

-- Agent Weights History: Track weight changes over time for learning system
CREATE TABLE IF NOT EXISTS agent_weights_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    agent_name VARCHAR(50) NOT NULL,
    weight DECIMAL(4,2) NOT NULL,
    win_rate_7d DECIMAL(5,2),
    win_rate_30d DECIMAL(5,2),
    win_rate_90d DECIMAL(5,2),
    trades_count_7d INTEGER DEFAULT 0,
    trades_count_30d INTEGER DEFAULT 0,
    trades_count_90d INTEGER DEFAULT 0,
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Learning Log: Record all learning system events
CREATE TABLE IF NOT EXISTS learning_log (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    event_type VARCHAR(30) NOT NULL, -- WEIGHT_UPDATE, BIAS_DETECTED, CORRECTION_APPLIED, REGIME_SHIFT, FREEZE, ALERT
    agent_name VARCHAR(50),
    metric_name VARCHAR(50),
    old_value DECIMAL(10,4),
    new_value DECIMAL(10,4),
    reasoning TEXT,
    bias_type VARCHAR(30), -- OVERFITTING, RECENCY, THRASHING, REGIME_BLINDNESS
    correction_applied TEXT,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- System Config: Configuration settings for learning system
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
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

-- Learning system indexes
CREATE INDEX IF NOT EXISTS idx_agent_weights_history_date ON agent_weights_history(date DESC);
CREATE INDEX IF NOT EXISTS idx_agent_weights_history_agent ON agent_weights_history(agent_name);
CREATE INDEX IF NOT EXISTS idx_learning_log_date ON learning_log(date DESC);
CREATE INDEX IF NOT EXISTS idx_learning_log_event_type ON learning_log(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_log_agent ON learning_log(agent_name);
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

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

-- Seed initial system config for learning system
INSERT INTO system_config (config_key, config_value, description) VALUES
    ('AUTO_LEARNING_ENABLED', 'false', 'Enable automatic weight optimization without human review'),
    ('HUMAN_REVIEW_REQUIRED', 'true', 'Require human review before applying weight changes'),
    ('MIN_CONFIDENCE_FOR_AUTO', '0.80', 'Minimum confidence level for automatic weight application'),
    ('MAX_WEIGHT_CHANGE_DAILY', '0.10', 'Maximum allowed weight change per day (10%)'),
    ('WEIGHT_MIN_BOUND', '0.30', 'Minimum allowed agent weight'),
    ('WEIGHT_MAX_BOUND', '2.00', 'Maximum allowed agent weight'),
    ('LEARNING_TIMEFRAME_WEIGHTS', '{"7d": 0.4, "30d": 0.4, "90d": 0.2}', 'Weights for different time periods in performance calculation'),
    ('FREEZE_DURATION_DAYS', '3', 'Number of days to freeze weights when thrashing detected')
ON CONFLICT (config_key) DO NOTHING;

-- Seed initial agent weights
INSERT INTO agent_weights_history (date, agent_name, weight, reasoning) VALUES
    (CURRENT_DATE, 'ContrarianAgent', 1.00, 'Initial default weight'),
    (CURRENT_DATE, 'GrowthAgent', 1.00, 'Initial default weight'),
    (CURRENT_DATE, 'MultiModalAgent', 1.00, 'Initial default weight'),
    (CURRENT_DATE, 'PredictorAgent', 1.00, 'Initial default weight')
ON CONFLICT DO NOTHING;
