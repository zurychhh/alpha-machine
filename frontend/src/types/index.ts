export interface AgentAnalysis {
  id: number
  agent_name: string
  recommendation: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  reasoning: string
  data_used: Record<string, unknown>
  timestamp: string
}

export interface Signal {
  id: number
  ticker: string
  signal_type: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  entry_price: number | null
  target_price: number | null
  stop_loss: number | null
  position_size: number
  status: 'PENDING' | 'APPROVED' | 'EXECUTED' | 'CLOSED'
  timestamp: string
  executed_at: string | null
  closed_at: string | null
  pnl: number | null
  notes: string | null
  agent_analyses: AgentAnalysis[]
}

export interface SignalStatistics {
  period_days: number
  total_signals: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  closed_signals: number
  win_rate: number | null
  average_pnl: number | null
}

export interface MarketData {
  ticker: string
  current_price: number
  open_price: number
  high_price: number
  low_price: number
  volume: number
  change_percent: number
  market_cap: number
  timestamp: string
}

export interface WatchlistItem {
  id: number
  ticker: string
  company_name: string
  sector: string
  is_active: boolean
  added_at: string
}

export interface AgentInfo {
  name: string
  description: string
  strategy_type: string
}

export interface GenerateSignalRequest {
  ticker: string
  include_reasoning?: boolean
}

export interface GenerateSignalResponse {
  ticker: string
  status: string
  signal: string
  confidence: number
  reasoning: string
  signal_id?: number
}

export interface ApiError {
  detail: string
}

export type SignalType = 'BUY' | 'SELL' | 'HOLD'
export type SignalStatus = 'PENDING' | 'APPROVED' | 'EXECUTED' | 'CLOSED'
