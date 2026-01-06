import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Portfolio from './pages/Portfolio'
import SignalDetails from './pages/SignalDetails'
import PaperTrading from './pages/PaperTrading'
import Learning from './pages/Learning'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route path="paper-trading" element={<PaperTrading />} />
        <Route path="learning" element={<Learning />} />
        <Route path="signals/:signalId" element={<SignalDetails />} />
      </Route>
    </Routes>
  )
}

export default App
