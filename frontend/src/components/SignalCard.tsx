import { Link } from 'react-router-dom'
import type { Signal } from '../types'
import ConfidenceStars from './ConfidenceStars'

interface SignalCardProps {
  signal: Signal
  onClick?: () => void
}

function SignalCard({ signal, onClick }: SignalCardProps) {
  const getSignalColor = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return 'signal-buy'
      case 'SELL':
        return 'signal-sell'
      default:
        return 'signal-hold'
    }
  }

  const getSignalIcon = (signalType: string) => {
    switch (signalType) {
      case 'BUY':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        )
      case 'SELL':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        )
    }
  }

  const formatPrice = (price: number | null) => {
    if (price === null) return '-'
    return `$${price.toFixed(2)}`
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <div
      className={`signal-card cursor-pointer ${getSignalColor(signal.signal_type)}`}
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg font-bold">{signal.ticker}</span>
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSignalColor(signal.signal_type)}`}
          >
            {getSignalIcon(signal.signal_type)}
            <span className="ml-1">{signal.signal_type}</span>
          </span>
        </div>
        <span
          className={`text-xs px-2 py-1 rounded ${
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

      <div className="mb-3">
        <ConfidenceStars confidence={signal.confidence} showLabel />
      </div>

      <div className="grid grid-cols-3 gap-2 text-sm mb-3">
        <div>
          <span className="text-gray-500">Entry</span>
          <div className="font-medium">{formatPrice(signal.entry_price)}</div>
        </div>
        <div>
          <span className="text-gray-500">Target</span>
          <div className="font-medium text-green-600">
            {formatPrice(signal.target_price)}
          </div>
        </div>
        <div>
          <span className="text-gray-500">Stop</span>
          <div className="font-medium text-red-600">
            {formatPrice(signal.stop_loss)}
          </div>
        </div>
      </div>

      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>{formatDate(signal.timestamp)}</span>
        <Link
          to={`/signals/${signal.id}`}
          className="text-primary-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          View Details
        </Link>
      </div>
    </div>
  )
}

export default SignalCard
