import { Link, Navigate, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { CustomerLogin, CustomerSignup } from './pages/Customer/Auth'
import { CustomerScan } from './pages/Customer/Scan'
import { CustomerCart } from './pages/Customer/Cart'
import { CustomerHistory } from './pages/Customer/History'
import { OfficialLogin } from './pages/Official/Auth'
import { OfficialFetchBill } from './pages/Official/FetchBill'
import { OfficialDashboard } from './pages/Official/Dashboard'
import { getTokens, logout } from './lib/auth'

function Nav() {
  const [role, setRole] = useState<string | null>(null)
  useEffect(() => {
    const t = getTokens()
    setRole(t?.role ?? null)
  }, [])
  return (
    <nav className="flex items-center justify-between p-4 bg-white shadow">
      <div className="flex gap-4">
        <Link to="/" className="font-semibold">Self-Checkout</Link>
        <Link to="/customer/scan" className="text-blue-600">Scan</Link>
        <Link to="/customer/cart" className="text-blue-600">Cart</Link>
        {role === 'customer' && (
          <Link to="/customer/history" className="text-blue-600">History</Link>
        )}
        {(role === 'cashier' || role === 'admin') && (
          <>
            <Link to="/official/dashboard" className="text-purple-700">Official Dashboard</Link>
            <Link to="/official/fetch" className="text-purple-700">Scan Invoice</Link>
          </>
        )}
      </div>
      <div className="flex gap-3 items-center">
        {role ? (
          <>
            <span className="text-sm text-gray-600">{role}</span>
            <button onClick={() => { logout(); window.location.href = '/' }} className="px-3 py-1 rounded bg-gray-100 hover:bg-gray-200">Logout</button>
          </>
        ) : (
          <>
            <Link to="/customer/login" className="px-3 py-1 rounded bg-blue-600 text-white">Login / Register (Google)</Link>
          </>
        )}
      </div>
    </nav>
  )
}

function Home() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-2">Welcome</h1>
      <p className="text-gray-600">Scan product codes, add to cart, login with Google to generate a bill QR, and pay at the official counter.</p>
    </div>
  )
}

export default function App() {
  return (
    <div className="min-h-screen">
      <Nav />
      <Routes>
        <Route path="/" element={<Home />} />

        <Route path="/customer/login" element={<CustomerLogin />} />
        <Route path="/customer/signup" element={<CustomerSignup />} />
        <Route path="/customer/scan" element={<CustomerScan />} />
        <Route path="/customer/cart" element={<CustomerCart />} />
        <Route path="/customer/history" element={<CustomerHistory />} />

        {/* Secret official login route, not linked from nav */}
        <Route path="/official-login" element={<OfficialLogin />} />
        <Route path="/official/fetch" element={<OfficialFetchBill />} />
        <Route path="/official/dashboard" element={<OfficialDashboard />} />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  )
}

