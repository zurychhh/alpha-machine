-- Migration: Add backtest_results table
-- Date: 2026-01-04
-- Description: Creates backtest_results table for storing backtesting simulation results

-- Create backtest_results table
CREATE TABLE IF NOT EXISTS backtest_results (
    id SERIAL PRIMARY KEY,
    backtest_id VARCHAR(50) NOT NULL,
    signal_id INTEGER NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE NOT NULL,
    entry_price DECIMAL(10,2) NOT NULL,
    exit_price DECIMAL(10,2) NOT NULL,
    shares INTEGER NOT NULL,
    pnl DECIMAL(10,2) NOT NULL,
    pnl_pct DECIMAL(7,3) NOT NULL,
    trade_result VARCHAR(10) NOT NULL,
    days_held INTEGER NOT NULL,
    exit_reason VARCHAR(20),
    position_type VARCHAR(20),
    allocation_pct DECIMAL(5,3),
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_backtest_results_backtest_id ON backtest_results(backtest_id);
CREATE INDEX IF NOT EXISTS idx_backtest_results_signal_id ON backtest_results(signal_id);

-- Rollback command (run this to undo migration):
-- DROP INDEX IF EXISTS idx_backtest_results_backtest_id;
-- DROP INDEX IF EXISTS idx_backtest_results_signal_id;
-- DROP TABLE IF EXISTS backtest_results;
