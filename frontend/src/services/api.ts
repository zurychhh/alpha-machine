import type {
  Signal,
  SignalStatistics,
  MarketData,
  WatchlistItem,
  AgentInfo,
  GenerateSignalRequest,
  GenerateSignalResponse,
  PaperTradingData,
  WeightsResponse,
  WeightHistoryResponse,
  BiasCheckResponse,
  LearningLogsResponse,
  LogSummaryResponse,
  LearningConfigResponse,
  OptimizationPreview,
  WeightOverrideRequest,
} from '../types'

const API_BASE = '/api/v1'

class ApiClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Signals
  async getSignals(params?: {
    ticker?: string
    signal_type?: string
    status?: string
    days?: number
    limit?: number
    offset?: number
  }): Promise<Signal[]> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    const response = await this.request<{ count: number; signals: Signal[] }>(
      `/signals${query ? `?${query}` : ''}`
    )
    return response.signals
  }

  async getSignal(signalId: number): Promise<Signal> {
    return this.request<Signal>(`/signals/${signalId}`)
  }

  async getSignalStatistics(days?: number): Promise<SignalStatistics> {
    const query = days ? `?days=${days}` : ''
    return this.request<SignalStatistics>(`/signals/stats${query}`)
  }

  // Paper Trading
  async getPaperTradingData(days?: number): Promise<PaperTradingData> {
    const query = days ? `?days=${days}` : ''
    return this.request<PaperTradingData>(`/signals/paper-trading${query}`)
  }

  async getAgents(): Promise<AgentInfo[]> {
    return this.request<AgentInfo[]>('/signals/agents')
  }

  async generateSignal(
    data: GenerateSignalRequest
  ): Promise<GenerateSignalResponse> {
    return this.request<GenerateSignalResponse>('/signals/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateSignalStatus(
    signalId: number,
    status: string,
    pnl?: number,
    notes?: string
  ): Promise<Signal> {
    return this.request<Signal>(`/signals/${signalId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, pnl, notes }),
    })
  }

  // Market Data
  async getMarketData(ticker: string): Promise<MarketData> {
    return this.request<MarketData>(`/market-data/${ticker}`)
  }

  async getTechnicalIndicators(ticker: string): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>(`/market-data/${ticker}/technicals`)
  }

  // Watchlist
  async getWatchlist(): Promise<WatchlistItem[]> {
    return this.request<WatchlistItem[]>('/watchlist')
  }

  async addToWatchlist(ticker: string): Promise<WatchlistItem> {
    return this.request<WatchlistItem>('/watchlist', {
      method: 'POST',
      body: JSON.stringify({ ticker }),
    })
  }

  async removeFromWatchlist(ticker: string): Promise<void> {
    return this.request<void>(`/watchlist/${ticker}`, {
      method: 'DELETE',
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health')
  }

  // Learning System
  async getLearningWeights(): Promise<WeightsResponse> {
    return this.request<WeightsResponse>('/learning/weights/current')
  }

  async getLearningWeightHistory(params?: {
    agent_name?: string
    days?: number
  }): Promise<WeightHistoryResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    return this.request<WeightHistoryResponse>(
      `/learning/weights/history${query ? `?${query}` : ''}`
    )
  }

  async checkBiases(): Promise<BiasCheckResponse> {
    return this.request<BiasCheckResponse>('/learning/biases/check')
  }

  async getLearningLogs(params?: {
    event_type?: string
    agent_name?: string
    days?: number
    limit?: number
    offset?: number
  }): Promise<LearningLogsResponse> {
    const searchParams = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, String(value))
        }
      })
    }
    const query = searchParams.toString()
    return this.request<LearningLogsResponse>(
      `/learning/logs${query ? `?${query}` : ''}`
    )
  }

  async getLearningLogSummary(days?: number): Promise<LogSummaryResponse> {
    const query = days ? `?days=${days}` : ''
    return this.request<LogSummaryResponse>(`/learning/logs/summary${query}`)
  }

  async getLearningConfig(): Promise<LearningConfigResponse> {
    return this.request<LearningConfigResponse>('/learning/config')
  }

  async getOptimizationPreview(): Promise<OptimizationPreview> {
    return this.request<OptimizationPreview>('/learning/optimize/preview')
  }

  async overrideWeight(data: WeightOverrideRequest): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>('/learning/weights/override', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async triggerOptimization(apply_weights: boolean = false, force: boolean = false): Promise<{ status: string; task_id: string }> {
    return this.request<{ status: string; task_id: string }>('/learning/optimize/trigger', {
      method: 'POST',
      body: JSON.stringify({ apply_weights, force }),
    })
  }
}

export const api = new ApiClient()
export default api
