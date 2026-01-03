import { useState, useEffect } from 'react'
import type { Signal, SignalStatistics } from '../types'
import api from '../services/api'
import SignalCard from '../components/SignalCard'
import SignalDetailsModal from '../components/SignalDetailsModal'

function Dashboard() {
  const [signals, setSignals] = useState<Signal[]>([])
  const [stats, setStats] = useState<SignalStatistics | null>(null)
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'BUY' | 'SELL' | 'HOLD'>('all')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [signalsData, statsData] = await Promise.all([
        api.getSignals({ limit: 50 }),
        api.getSignalStatistics(30),
      ])
      setSignals(signalsData)
      setStats(statsData)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (signalId: number) => {
    try {
      await api.updateSignalStatus(signalId, 'APPROVED')
      await loadData()
      setSelectedSignal(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve signal')
    }
  }

  const filteredSignals = filter === 'all'
    ? signals
    : signals.filter((s) => s.signal_type === filter)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error}</p>
        <button
          onClick={loadData}
          className="mt-2 text-sm text-red-600 hover:underline"
        >
          Try again
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">AI-generated trading signals</p>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Total Signals (30d)</div>
            <div className="text-2xl font-bold">{stats.total_signals}</div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Win Rate</div>
            <div className="text-2xl font-bold text-green-600">
              {stats.win_rate !== null
                ? `${(stats.win_rate * 100).toFixed(1)}%`
                : '-'}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Avg P&L</div>
            <div
              className={`text-2xl font-bold ${
                (stats.average_pnl ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {stats.average_pnl !== null
                ? `$${stats.average_pnl.toFixed(2)}`
                : '-'}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="text-sm text-gray-500">Closed Trades</div>
            <div className="text-2xl font-bold">{stats.closed_signals}</div>
          </div>
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <div className="flex space-x-2">
          {(['all', 'BUY', 'SELL', 'HOLD'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                filter === type
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {type === 'all' ? 'All' : type}
            </button>
          ))}
        </div>
        <button onClick={loadData} className="btn-secondary text-sm">
          Refresh
        </button>
      </div>

      {filteredSignals.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">No signals found</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSignals.map((signal) => (
            <SignalCard
              key={signal.id}
              signal={signal}
              onClick={() => setSelectedSignal(signal)}
            />
          ))}
        </div>
      )}

      {selectedSignal && (
        <SignalDetailsModal
          signal={selectedSignal}
          onClose={() => setSelectedSignal(null)}
          onApprove={handleApprove}
        />
      )}
    </div>
  )
}

export default Dashboard
