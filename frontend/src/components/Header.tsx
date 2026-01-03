import { Link, useLocation } from 'react-router-dom'

function Header() {
  const location = useLocation()

  const isActive = (path: string) => {
    return location.pathname === path
      ? 'text-primary-600 border-b-2 border-primary-600'
      : 'text-gray-600 hover:text-primary-600'
  }

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <svg
                className="w-8 h-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
                />
              </svg>
              <span className="text-xl font-bold text-gray-900">
                Alpha Machine
              </span>
            </Link>
          </div>

          <nav className="flex space-x-8">
            <Link
              to="/"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${isActive('/')}`}
            >
              Dashboard
            </Link>
            <Link
              to="/portfolio"
              className={`inline-flex items-center px-1 pt-1 text-sm font-medium ${isActive('/portfolio')}`}
            >
              Portfolio
            </Link>
          </nav>

          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">
              AI Trading Signals
            </span>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
