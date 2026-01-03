import { useState, useEffect } from 'react'
import type { Signal } from '../types'
import api from '../services/api'
import ConfidenceStars from '../components/ConfidenceStars'

function Portfolio() {
  const [executedSignals, setExecutedSignals] = useState<Signal[]>([])
  const [closedSignals, setClosedSignals] = useState<Signal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [view, setView] = useState<'executed' | 'closed'>('executed')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [executed, closed] = await Promise.all([
        api.getSignals({ status: 'EXECUTED', limit: 50 }),
        api.getSignals({ status: 'CLOSED', limit: 50 }),
      ])
      setExecutedSignals(executed)
      setClosedSignals(closed)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = async (signalId: number, pnl: number) => {
    try {
      await api.updateSignalStatus(signalId, 'CLOSED', pnl)
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to close position')
    }
  }

  const formatPrice = (price: number | null) => {
    if (price === null) return '-'
    return `$${price.toFixed(2)}`
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const totalPnL = closedSignals.reduce(
    (sum, s) => sum + (s.pnl ?? 0),
    0
  )

  const winningTrades = closedSignals.filter((s) => (s.pnl ?? 0) > 0).length
  const winRate =
    closedSignals.length > 0
      ? ((winningTrades / closedSignals.length) * 100).toFixed(1)
      : '-'

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

  const displaySignals = view === 'executed' ? executedSignals : closedSignals

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Portfolio</h1>
        <p className="text-gray-600">Track your trading positions</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Active Positions</div>
          <div className="text-2xl font-bold">{executedSignals.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total P&L</div>
          <div
            className={`text-2xl font-bold ${
              totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            ${totalPnL.toFixed(2)}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Win Rate</div>
          <div className="text-2xl font-bold text-primary-600">{winRate}%</div>
        </div>
      </div>

      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setView('executed')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            view === 'executed'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Active ({executedSignals.length})
        </button>
        <button
          onClick={() => setView('closed')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            view === 'closed'
              ? 'bg-primary-600 text-white'
              : 'bg-white text-gray-700 hover:bg-gray-100'
          }`}
        >
          Closed ({closedSignals.length})
        </button>
      </div>

      {displaySignals.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">
            {view === 'executed'
              ? 'No active positions'
              : 'No closed trades yet'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Ticker
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Entry
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Target
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Shares
                </th>
                {view === 'closed' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    P&L
                  </th>
                )}
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Date
                </th>
                {view === 'executed' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {displaySignals.map((signal) => (
                <tr key={signal.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="font-medium">{signal.ticker}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        signal.signal_type === 'BUY'
                          ? 'bg-green-100 text-green-800'
                          : signal.signal_type === 'SELL'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {signal.signal_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <ConfidenceStars confidence={signal.confidence} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {formatPrice(signal.entry_price)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-green-600">
                    {formatPrice(signal.target_price)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {signal.position_size}
                  </td>
                  {view === 'closed' && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`font-medium ${
                          (signal.pnl ?? 0) >= 0
                            ? 'text-green-600'
                            : 'text-red-600'
                        }`}
                      >
                        ${(signal.pnl ?? 0).toFixed(2)}
                      </span>
                    </td>
                  )}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(
                      view === 'executed' ? signal.executed_at : signal.closed_at
                    )}
                  </td>
                  {view === 'executed' && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => {
                          const pnl = prompt('Enter P&L amount:')
                          if (pnl !== null) {
                            handleClose(signal.id, parseFloat(pnl))
                          }
                        }}
                        className="text-primary-600 hover:underline text-sm"
                      >
                        Close Position
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Portfolio
