import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { Signal } from '../types'
import api from '../services/api'
import ConfidenceStars from '../components/ConfidenceStars'

function SignalDetails() {
  const { signalId } = useParams<{ signalId: string }>()
  const navigate = useNavigate()
  const [signal, setSignal] = useState<Signal | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (signalId) {
      loadSignal(parseInt(signalId))
    }
  }, [signalId])

  const loadSignal = async (id: number) => {
    try {
      setLoading(true)
      const data = await api.getSignal(id)
      setSignal(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load signal')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!signal) return
    try {
      await api.updateSignalStatus(signal.id, 'APPROVED')
      await loadSignal(signal.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve signal')
    }
  }

  const handleExecute = async () => {
    if (!signal) return
    try {
      await api.updateSignalStatus(signal.id, 'EXECUTED')
      await loadSignal(signal.id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute signal')
    }
  }

  const formatPrice = (price: number | null) => {
    if (price === null) return '-'
    return `$${price.toFixed(2)}`
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getAgentColor = (recommendation: string) => {
    switch (recommendation) {
      case 'BUY':
      case 'STRONG_BUY':
        return 'border-green-200 bg-green-50'
      case 'SELL':
      case 'STRONG_SELL':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-yellow-200 bg-yellow-50'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !signal) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">{error || 'Signal not found'}</p>
        <button
          onClick={() => navigate('/')}
          className="mt-2 text-sm text-red-600 hover:underline"
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div>
      <button
        onClick={() => navigate('/')}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
      >
        <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        Back to Dashboard
      </button>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="flex justify-between items-start mb-6">
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-3xl font-bold text-gray-900">{signal.ticker}</h1>
              <span
                className={`px-3 py-1 rounded-full text-lg font-medium ${
                  signal.signal_type === 'BUY'
                    ? 'bg-green-100 text-green-800'
                    : signal.signal_type === 'SELL'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {signal.signal_type}
              </span>
            </div>
            <p className="text-gray-500 mt-1">Signal ID: {signal.id}</p>
          </div>
          <span
            className={`px-4 py-2 rounded-full text-sm font-medium ${
              signal.status === 'PENDING'
                ? 'bg-yellow-100 text-yellow-800'
                : signal.status === 'APPROVED'
                ? 'bg-blue-100 text-blue-800'
                : signal.status === 'EXECUTED'
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            {signal.status}
          </span>
        </div>

        <div className="mb-6">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Confidence Level</h3>
          <ConfidenceStars confidence={signal.confidence} showLabel />
        </div>

        <div className="grid grid-cols-4 gap-6 mb-8 bg-gray-50 rounded-lg p-6">
          <div className="text-center">
            <div className="text-sm text-gray-500">Entry Price</div>
            <div className="text-2xl font-bold">{formatPrice(signal.entry_price)}</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Target Price</div>
            <div className="text-2xl font-bold text-green-600">
              {formatPrice(signal.target_price)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Stop Loss</div>
            <div className="text-2xl font-bold text-red-600">
              {formatPrice(signal.stop_loss)}
            </div>
          </div>
          <div className="text-center">
            <div className="text-sm text-gray-500">Position Size</div>
            <div className="text-2xl font-bold">{signal.position_size} shares</div>
          </div>
        </div>

        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Agent Analyses</h2>
          {signal.agent_analyses.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {signal.agent_analyses.map((analysis) => (
                <div
                  key={analysis.id}
                  className={`border rounded-lg p-4 ${getAgentColor(analysis.recommendation)}`}
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-semibold text-gray-900">
                        {analysis.agent_name}
                      </h3>
                      <span
                        className={`inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium ${
                          analysis.recommendation === 'BUY'
                            ? 'bg-green-200 text-green-800'
                            : analysis.recommendation === 'SELL'
                            ? 'bg-red-200 text-red-800'
                            : 'bg-yellow-200 text-yellow-800'
                        }`}
                      >
                        {analysis.recommendation}
                      </span>
                    </div>
                    <ConfidenceStars confidence={analysis.confidence} />
                  </div>
                  <p className="text-sm text-gray-700">{analysis.reasoning}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No agent analyses available</p>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 mb-8 text-sm">
          <div className="bg-gray-50 rounded-lg p-4">
            <span className="text-gray-500">Created:</span>
            <span className="ml-2 font-medium">{formatDate(signal.timestamp)}</span>
          </div>
          {signal.executed_at && (
            <div className="bg-gray-50 rounded-lg p-4">
              <span className="text-gray-500">Executed:</span>
              <span className="ml-2 font-medium">{formatDate(signal.executed_at)}</span>
            </div>
          )}
          {signal.closed_at && (
            <div className="bg-gray-50 rounded-lg p-4">
              <span className="text-gray-500">Closed:</span>
              <span className="ml-2 font-medium">{formatDate(signal.closed_at)}</span>
            </div>
          )}
          {signal.pnl !== null && (
            <div className="bg-gray-50 rounded-lg p-4">
              <span className="text-gray-500">P&L:</span>
              <span
                className={`ml-2 font-bold ${
                  signal.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                ${signal.pnl.toFixed(2)}
              </span>
            </div>
          )}
        </div>

        {signal.notes && (
          <div className="mb-8">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Notes</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-gray-700">{signal.notes}</p>
            </div>
          </div>
        )}

        {signal.status === 'PENDING' && (
          <div className="flex justify-end space-x-3 border-t pt-6">
            <button
              onClick={handleApprove}
              className="btn-primary"
            >
              Approve Signal
            </button>
          </div>
        )}

        {signal.status === 'APPROVED' && (
          <div className="flex justify-end space-x-3 border-t pt-6">
            <button
              onClick={handleExecute}
              className="btn-primary bg-green-600 hover:bg-green-700"
            >
              Execute Trade
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default SignalDetails
