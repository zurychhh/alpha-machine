import type {
  Signal,
  SignalStatistics,
  MarketData,
  WatchlistItem,
  AgentInfo,
  GenerateSignalRequest,
  GenerateSignalResponse,
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
    return this.request<Signal[]>(`/signals${query ? `?${query}` : ''}`)
  }

  async getSignal(signalId: number): Promise<Signal> {
    return this.request<Signal>(`/signals/${signalId}`)
  }

  async getSignalStatistics(days?: number): Promise<SignalStatistics> {
    const query = days ? `?days=${days}` : ''
    return this.request<SignalStatistics>(`/signals/stats${query}`)
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
}

export const api = new ApiClient()
export default api
