import type { Signal } from '../types'
import ConfidenceStars from './ConfidenceStars'

interface SignalDetailsModalProps {
  signal: Signal
  onClose: () => void
  onApprove?: (signalId: number) => void
  onReject?: (signalId: number) => void
}

function SignalDetailsModal({
  signal,
  onClose,
  onApprove,
  onReject,
}: SignalDetailsModalProps) {
  const formatPrice = (price: number | null) => {
    if (price === null) return '-'
    return `$${price.toFixed(2)}`
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getAgentColor = (recommendation: string) => {
    switch (recommendation) {
      case 'BUY':
      case 'STRONG_BUY':
        return 'text-green-600 bg-green-50'
      case 'SELL':
      case 'STRONG_SELL':
        return 'text-red-600 bg-red-50'
      default:
        return 'text-yellow-600 bg-yellow-50'
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {signal.ticker} - {signal.signal_type}
              </h2>
              <p className="text-sm text-gray-500 mt-1">
                Signal ID: {signal.id}
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">
                Confidence Level
              </h3>
              <ConfidenceStars confidence={signal.confidence} showLabel />
            </div>
            <div>
              <h3 className="text-sm font-medium text-gray-500 mb-2">Status</h3>
              <span
                className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
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
          </div>

          <div className="grid grid-cols-3 gap-4 mb-6 bg-gray-50 rounded-lg p-4">
            <div className="text-center">
              <div className="text-sm text-gray-500">Entry Price</div>
              <div className="text-xl font-bold">
                {formatPrice(signal.entry_price)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Target Price</div>
              <div className="text-xl font-bold text-green-600">
                {formatPrice(signal.target_price)}
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm text-gray-500">Stop Loss</div>
              <div className="text-xl font-bold text-red-600">
                {formatPrice(signal.stop_loss)}
              </div>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">
              Agent Analyses
            </h3>
            {signal.agent_analyses.length > 0 ? (
              <div className="space-y-3">
                {signal.agent_analyses.map((analysis) => (
                  <div
                    key={analysis.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{analysis.agent_name}</span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-medium ${getAgentColor(analysis.recommendation)}`}
                        >
                          {analysis.recommendation}
                        </span>
                      </div>
                      <ConfidenceStars confidence={analysis.confidence} />
                    </div>
                    <p className="text-sm text-gray-600">{analysis.reasoning}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No agent analyses available</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
            <div>
              <span className="text-gray-500">Position Size:</span>
              <span className="ml-2 font-medium">{signal.position_size} shares</span>
            </div>
            <div>
              <span className="text-gray-500">Created:</span>
              <span className="ml-2">{formatDate(signal.timestamp)}</span>
            </div>
            {signal.executed_at && (
              <div>
                <span className="text-gray-500">Executed:</span>
                <span className="ml-2">{formatDate(signal.executed_at)}</span>
              </div>
            )}
            {signal.closed_at && (
              <div>
                <span className="text-gray-500">Closed:</span>
                <span className="ml-2">{formatDate(signal.closed_at)}</span>
              </div>
            )}
            {signal.pnl !== null && (
              <div>
                <span className="text-gray-500">P&L:</span>
                <span
                  className={`ml-2 font-medium ${
                    signal.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  ${signal.pnl.toFixed(2)}
                </span>
              </div>
            )}
          </div>

          {signal.notes && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Notes</h3>
              <p className="text-sm text-gray-700 bg-gray-50 rounded p-3">
                {signal.notes}
              </p>
            </div>
          )}

          {signal.status === 'PENDING' && (onApprove || onReject) && (
            <div className="flex justify-end space-x-3 border-t pt-4">
              {onReject && (
                <button
                  onClick={() => onReject(signal.id)}
                  className="btn-secondary"
                >
                  Reject
                </button>
              )}
              {onApprove && (
                <button
                  onClick={() => onApprove(signal.id)}
                  className="btn-primary"
                >
                  Approve Signal
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SignalDetailsModal
