/**
 * Learning Dashboard - Self-Learning System Interface
 *
 * View agent weights, performance metrics, bias detection, and manage overrides.
 * v1.0.0 - 2026-01-06
 */

import { useState, useEffect } from 'react'
import type {
  AgentWeight,
  BiasCheckResponse,
  LearningLogEntry,
} from '../types'
import api from '../services/api'

function Learning() {
  const [weights, setWeights] = useState<AgentWeight[]>([])
  const [biases, setBiases] = useState<BiasCheckResponse | null>(null)
  const [logs, setLogs] = useState<LearningLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [overrideForm, setOverrideForm] = useState({
    agent_name: '',
    new_weight: 1.0,
    reason: '',
  })
  const [overrideStatus, setOverrideStatus] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [weightsRes, biasesRes, logsRes] = await Promise.all([
        api.getLearningWeights(),
        api.checkBiases(),
        api.getLearningLogs({ days: 7, limit: 10 }),
      ])
      setWeights(weightsRes.weights || [])
      setBiases(biasesRes)
      setLogs(logsRes.logs || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleOverride = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!overrideForm.agent_name || !overrideForm.reason || overrideForm.reason.length < 10) {
      setOverrideStatus('Error: Agent name and reason (min 10 chars) required')
      return
    }
    try {
      const result = await api.overrideWeight(overrideForm)
      setOverrideStatus(`Success: ${result.message}`)
      setOverrideForm({ agent_name: '', new_weight: 1.0, reason: '' })
      loadData()
    } catch (err) {
      setOverrideStatus(`Error: ${err instanceof Error ? err.message : 'Failed'}`)
    }
  }

  const getBiasColor = (severity: number) => {
    if (severity >= 0.7) return 'bg-red-100 text-red-800 border-red-300'
    if (severity >= 0.4) return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    return 'bg-blue-100 text-blue-800 border-blue-300'
  }

  const getBiasBadge = (type: string) => {
    const badges: Record<string, string> = {
      OVERFITTING: 'bg-purple-100 text-purple-800',
      RECENCY: 'bg-orange-100 text-orange-800',
      THRASHING: 'bg-red-100 text-red-800',
      REGIME_BLINDNESS: 'bg-blue-100 text-blue-800',
    }
    return badges[type] || 'bg-gray-100 text-gray-800'
  }

  const getWeightColor = (weight: number) => {
    if (weight >= 1.5) return 'text-green-600 font-semibold'
    if (weight <= 0.5) return 'text-red-600 font-semibold'
    return 'text-gray-900'
  }

  const getWinRateColor = (rate: number | null) => {
    if (rate === null) return 'text-gray-400'
    if (rate >= 60) return 'text-green-600'
    if (rate >= 50) return 'text-gray-600'
    return 'text-red-600'
  }

  const getEventBadge = (type: string) => {
    const badges: Record<string, string> = {
      WEIGHT_UPDATE: 'bg-blue-100 text-blue-800',
      BIAS_DETECTED: 'bg-yellow-100 text-yellow-800',
      CORRECTION_APPLIED: 'bg-green-100 text-green-800',
      REGIME_SHIFT: 'bg-purple-100 text-purple-800',
      FREEZE: 'bg-red-100 text-red-800',
      ALERT: 'bg-orange-100 text-orange-800',
    }
    return badges[type] || 'bg-gray-100 text-gray-800'
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

  return (
    <div>
      {/* Header */}
      <div className="mb-6 flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Self-Learning System</h1>
          <p className="text-gray-600">Agent weights, bias detection, and optimization</p>
        </div>
        <button onClick={loadData} className="btn-secondary text-sm">
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Active Agents</div>
          <div className="text-2xl font-bold text-primary-600">{weights.length}</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Biases Detected</div>
          <div className={`text-2xl font-bold ${biases && biases.biases_detected > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
            {biases?.biases_detected || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">System Confidence</div>
          <div className={`text-2xl font-bold ${biases && biases.overall_confidence >= 0.7 ? 'text-green-600' : 'text-yellow-600'}`}>
            {biases ? `${(biases.overall_confidence * 100).toFixed(0)}%` : '-'}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm text-gray-500">Recent Events</div>
          <div className="text-2xl font-bold">{logs.length}</div>
        </div>
      </div>

      {/* Bias Alerts */}
      {biases && biases.biases.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Bias Alerts</h2>
          <div className="space-y-3">
            {biases.biases.map((bias, idx) => (
              <div key={idx} className={`border rounded-lg p-4 ${getBiasColor(bias.severity)}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getBiasBadge(bias.type)}`}>
                      {bias.type}
                    </span>
                    {bias.agent && (
                      <span className="text-sm font-medium">{bias.agent}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm">Severity: {(bias.severity * 100).toFixed(0)}%</span>
                    {bias.correction_available && (
                      <span className="text-xs bg-green-200 text-green-800 px-2 py-0.5 rounded">
                        Auto-correction available
                      </span>
                    )}
                  </div>
                </div>
                <p className="text-sm">{bias.description}</p>
              </div>
            ))}
          </div>
          {biases.recommendations.length > 0 && (
            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900 mb-2">Recommendations</h3>
              <ul className="list-disc list-inside text-sm text-blue-800">
                {biases.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Agent Weights Table */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Performance & Weights</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Agent</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Weight</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Win Rate (7d)</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Win Rate (30d)</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Win Rate (90d)</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Trades (7d)</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Updated</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {weights.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                    No weight data available. Run optimization to initialize.
                  </td>
                </tr>
              ) : (
                weights.map((agent) => (
                  <tr key={agent.agent_name} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{agent.agent_name}</td>
                    <td className={`px-4 py-3 text-center ${getWeightColor(agent.weight)}`}>
                      {agent.weight.toFixed(2)}
                    </td>
                    <td className={`px-4 py-3 text-center ${getWinRateColor(agent.win_rate_7d)}`}>
                      {agent.win_rate_7d !== null ? `${agent.win_rate_7d.toFixed(1)}%` : '-'}
                    </td>
                    <td className={`px-4 py-3 text-center ${getWinRateColor(agent.win_rate_30d)}`}>
                      {agent.win_rate_30d !== null ? `${agent.win_rate_30d.toFixed(1)}%` : '-'}
                    </td>
                    <td className={`px-4 py-3 text-center ${getWinRateColor(agent.win_rate_90d)}`}>
                      {agent.win_rate_90d !== null ? `${agent.win_rate_90d.toFixed(1)}%` : '-'}
                    </td>
                    <td className="px-4 py-3 text-center text-gray-600">
                      {agent.trades_count_7d || 0}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {agent.last_updated || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Learning Logs */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {logs.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              No learning activity recorded yet.
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {logs.map((log) => (
                <div key={log.id} className="px-4 py-3 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getEventBadge(log.event_type)}`}>
                        {log.event_type}
                      </span>
                      {log.agent_name && (
                        <span className="text-sm font-medium text-gray-700">{log.agent_name}</span>
                      )}
                    </div>
                    <span className="text-xs text-gray-400">{log.date}</span>
                  </div>
                  {log.reasoning && (
                    <p className="text-sm text-gray-600">{log.reasoning}</p>
                  )}
                  {log.old_value !== null && log.new_value !== null && (
                    <p className="text-xs text-gray-500 mt-1">
                      {log.metric_name}: {log.old_value.toFixed(2)} → {log.new_value.toFixed(2)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Manual Override Form */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Manual Weight Override</h2>
        <div className="bg-white rounded-lg shadow p-4">
          <form onSubmit={handleOverride} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Agent</label>
                <select
                  value={overrideForm.agent_name}
                  onChange={(e) => setOverrideForm({ ...overrideForm, agent_name: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">Select agent...</option>
                  <option value="ContrarianAgent">ContrarianAgent</option>
                  <option value="GrowthAgent">GrowthAgent</option>
                  <option value="MultiModalAgent">MultiModalAgent</option>
                  <option value="PredictorAgent">PredictorAgent</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  New Weight ({overrideForm.new_weight.toFixed(2)})
                </label>
                <input
                  type="range"
                  min="0.30"
                  max="2.00"
                  step="0.05"
                  value={overrideForm.new_weight}
                  onChange={(e) => setOverrideForm({ ...overrideForm, new_weight: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>0.30</span>
                  <span>1.00</span>
                  <span>2.00</span>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Reason (min 10 chars)</label>
                <input
                  type="text"
                  value={overrideForm.reason}
                  onChange={(e) => setOverrideForm({ ...overrideForm, reason: e.target.value })}
                  placeholder="e.g., Agent underperforming in current market"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <button
                type="submit"
                className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors"
              >
                Apply Override
              </button>
              {overrideStatus && (
                <span className={`text-sm ${overrideStatus.startsWith('Error') ? 'text-red-600' : 'text-green-600'}`}>
                  {overrideStatus}
                </span>
              )}
            </div>
          </form>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
        <h3 className="font-medium text-gray-900 mb-2">About Self-Learning</h3>
        <ul className="list-disc list-inside space-y-1">
          <li><strong>Weights:</strong> Range from 0.30 (low influence) to 2.00 (high influence)</li>
          <li><strong>Optimization:</strong> Runs daily at 00:00 EST based on rolling 7d/30d/90d performance</li>
          <li><strong>Bias Detection:</strong> System monitors for overfitting, recency bias, thrashing, and regime blindness</li>
          <li><strong>Manual Override:</strong> Use sparingly - system will auto-adjust based on performance</li>
        </ul>
      </div>
    </div>
  )
}

export default Learning
