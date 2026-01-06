/**
 * Paper Trading Dashboard - 14-Day Validation Interface
 *
 * Track signal performance in real-time without risking money.
 * Signals auto-update status: WIN (hit target), LOSS (hit stop), ACTIVE (in play)
 * v1.0.0 - 2026-01-06
 */

import { useState, useEffect } from 'react'
import type { PaperTradingData, PaperSignal, PaperDay } from '../types'
import api from '../services/api'

function PaperTrading() {
  const [data, setData] = useState<PaperTradingData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedDay, setExpandedDay] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const result = await api.getPaperTradingData(14)
      setData(result)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'WIN': return 'bg-green-100 text-green-800'
      case 'LOSS': return 'bg-red-100 text-red-800'
      case 'ACTIVE': return 'bg-blue-100 text-blue-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPnlColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600'
    if (pnl < 0) return 'text-red-600'
    return 'text-gray-600'
  }

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
        <button onClick={loadData} className="mt-2 text-sm text-red-600 hover:underline">
          Try again
        </button>
      </div>
    )
  }

  if (!data) return null

  const { summary, timeline, days_remaining } = data

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Paper Trading</h1>
          <p className="text-gray-600">14-Day Validation (Jan 5 - Jan 19, 2026)</p>
        </div>
        <button onClick={loadData} className="btn-secondary text-sm">
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Days Left</div>
          <div className="text-2xl font-bold text-primary-600">{days_remaining}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Total Signals</div>
          <div className="text-2xl font-bold">{summary.total_signals}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Win Rate</div>
          <div className={`text-2xl font-bold ${summary.win_rate !== null && summary.win_rate >= 50 ? 'text-green-600' : 'text-gray-600'}`}>
            {summary.win_rate !== null ? `${summary.win_rate}%` : '-'}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Record</div>
          <div className="text-lg font-bold">
            <span className="text-green-600">{summary.wins}W</span>
            {' / '}
            <span className="text-red-600">{summary.losses}L</span>
            {' / '}
            <span className="text-blue-600">{summary.active}A</span>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Simulated P&L</div>
          <div className={`text-2xl font-bold ${getPnlColor(summary.total_pnl)}`}>
            ${summary.total_pnl.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Day-by-Day Timeline</h2>
        {timeline.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
            No BUY signals in this period
          </div>
        ) : (
          <div className="space-y-2">
            {timeline.map((day: PaperDay) => (
              <div key={day.date} className="bg-white rounded-lg shadow">
                <button
                  onClick={() => setExpandedDay(expandedDay === day.date ? null : day.date)}
                  className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center space-x-4">
                    <span className="font-medium text-gray-900">{day.date}</span>
                    <span className="text-sm text-gray-500">{day.count} signals</span>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="flex space-x-2 text-sm">
                      <span className="text-green-600">{day.wins}W</span>
                      <span className="text-red-600">{day.losses}L</span>
                      <span className="text-blue-600">{day.active}A</span>
                    </div>
                    <span className={`font-medium ${getPnlColor(day.day_pnl)}`}>
                      ${day.day_pnl.toLocaleString()}
                    </span>
                    <svg
                      className={`w-5 h-5 text-gray-400 transition-transform ${expandedDay === day.date ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </div>
                </button>

                {expandedDay === day.date && (
                  <div className="border-t border-gray-200 px-4 py-3">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-gray-500">
                          <th className="pb-2">Ticker</th>
                          <th className="pb-2">Entry</th>
                          <th className="pb-2">Current</th>
                          <th className="pb-2">Target</th>
                          <th className="pb-2">Stop</th>
                          <th className="pb-2">Status</th>
                          <th className="pb-2 text-right">P&L</th>
                        </tr>
                      </thead>
                      <tbody>
                        {day.signals.map((sig: PaperSignal) => (
                          <tr key={sig.id} className="border-t border-gray-100">
                            <td className="py-2 font-medium">{sig.ticker}</td>
                            <td className="py-2">${sig.entry_price.toFixed(2)}</td>
                            <td className="py-2">
                              {sig.current_price ? `$${sig.current_price.toFixed(2)}` : '-'}
                            </td>
                            <td className="py-2 text-green-600">${sig.target_price.toFixed(2)}</td>
                            <td className="py-2 text-red-600">${sig.stop_loss.toFixed(2)}</td>
                            <td className="py-2">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(sig.paper_status)}`}>
                                {sig.paper_status}
                              </span>
                            </td>
                            <td className={`py-2 text-right font-medium ${getPnlColor(sig.paper_pnl)}`}>
                              ${sig.paper_pnl.toLocaleString()} ({sig.paper_pnl_percent > 0 ? '+' : ''}{sig.paper_pnl_percent}%)
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600">
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center">
            <span className="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
            WIN = Current price hit target (+25%)
          </div>
          <div className="flex items-center">
            <span className="w-3 h-3 rounded-full bg-red-500 mr-2"></span>
            LOSS = Current price hit stop-loss (-10%)
          </div>
          <div className="flex items-center">
            <span className="w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
            ACTIVE = Still in play
          </div>
        </div>
      </div>
    </div>
  )
}

export default PaperTrading
