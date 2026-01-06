-- Migration: Add learning system tables
-- Date: 2026-01-06
-- Description: Creates tables for agent weight optimization and meta-learning system
-- Tables: agent_weights_history, learning_log, system_config

-- Create agent_weights_history table
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

-- Create indexes for agent_weights_history
CREATE INDEX IF NOT EXISTS idx_agent_weights_history_date ON agent_weights_history(date);
CREATE INDEX IF NOT EXISTS idx_agent_weights_history_agent_name ON agent_weights_history(agent_name);
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_weights_history_unique
    ON agent_weights_history(date, agent_name);

-- Create learning_log table
CREATE TABLE IF NOT EXISTS learning_log (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    event_type VARCHAR(30) NOT NULL,
    agent_name VARCHAR(50),
    metric_name VARCHAR(50),
    old_value DECIMAL(10,4),
    new_value DECIMAL(10,4),
    reasoning TEXT,
    bias_type VARCHAR(30),
    correction_applied TEXT,
    confidence_level DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for learning_log
CREATE INDEX IF NOT EXISTS idx_learning_log_date ON learning_log(date);
CREATE INDEX IF NOT EXISTS idx_learning_log_event_type ON learning_log(event_type);
CREATE INDEX IF NOT EXISTS idx_learning_log_agent_name ON learning_log(agent_name);

-- Create system_config table
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for system_config
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- Insert default configuration values
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

-- Insert initial agent weights (all start at 1.0)
INSERT INTO agent_weights_history (date, agent_name, weight, reasoning) VALUES
    (CURRENT_DATE, 'ContrarianAgent', 1.00, 'Initial weight'),
    (CURRENT_DATE, 'GrowthAgent', 1.00, 'Initial weight'),
    (CURRENT_DATE, 'MultiModalAgent', 1.00, 'Initial weight'),
    (CURRENT_DATE, 'PredictorAgent', 1.00, 'Initial weight')
ON CONFLICT DO NOTHING;

-- Rollback command (run this to undo migration):
-- DROP INDEX IF EXISTS idx_agent_weights_history_date;
-- DROP INDEX IF EXISTS idx_agent_weights_history_agent_name;
-- DROP INDEX IF EXISTS idx_agent_weights_history_unique;
-- DROP TABLE IF EXISTS agent_weights_history;
-- DROP INDEX IF EXISTS idx_learning_log_date;
-- DROP INDEX IF EXISTS idx_learning_log_event_type;
-- DROP INDEX IF EXISTS idx_learning_log_agent_name;
-- DROP TABLE IF EXISTS learning_log;
-- DROP INDEX IF EXISTS idx_system_config_key;
-- DROP TABLE IF EXISTS system_config;
