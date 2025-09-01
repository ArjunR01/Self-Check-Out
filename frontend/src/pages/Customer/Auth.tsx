import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../lib/api'
import { setTokens } from '../../lib/auth'

export function CustomerLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [login, setLog] = useState(false);
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      const res = await api.post('/auth/customer/login', { email, password })
      setTokens(res.data.access_token, res.data.role)
      // navigate('/customer/cart')
      window.location.href = '/';
      setLog(true);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Login failed')
    }
  }

  async function loginWithGoogle() {
    setError(null)
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
    if (!clientId) {
      setError('Google OAuth not configured (missing VITE_GOOGLE_CLIENT_ID)')
      return
    }
    try {
      // @ts-ignore
      const google = (window as any).google
      if (!google?.accounts?.id) {
        setError('Google script not loaded. Please try again in a moment.')
        return
      }
      google.accounts.id.initialize({
        client_id: clientId,
        callback: async (response: any) => {
          try {
            const r = await api.post('/auth/customer/google', { id_token: response.credential })
            setTokens(r.data.access_token, r.data.role)
            navigate('/customer/cart')
          } catch (e: any) {
            setError(e?.response?.data?.detail || 'Google login failed')
          }
        }
      })
      google.accounts.id.prompt()
    } catch (e: any) {
      setError('Failed to start Google login')
    }
  }

  return (
    <div className="max-w-md mx-auto p-6">
      <h2 className="text-xl font-semibold mb-4">Customer Login</h2>
      <div className="space-y-3">
        {/* <button onClick={loginWithGoogle} className="w-full bg-red-500 text-white rounded p-2">Sign in with Google</button>
        <div className="text-xs text-gray-500">Google sign-in is required for customers. The form below is provided for local development.</div> */}
      </div>
      <form onSubmit={onSubmit} className="space-y-3 mt-4">
        <input className="w-full border rounded p-2" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="w-full border rounded p-2" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <button className="w-full bg-blue-600 text-white rounded p-2">Login</button>
      </form>
      <p className="text-sm text-gray-600 mt-3">No account? You can sign up below.</p>
      <CustomerSignup compact/>
    </div>
  )
}

export function CustomerSignup({ compact = false }: { compact?: boolean }) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    try {
      await api.post('/auth/customer/signup', { name, email, phone, password })
      setSuccess('Account created. You can now log in.')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Signup failed')
    }
  }

  return (
    <div className={compact ? 'mt-4' : 'max-w-md mx-auto p-6'}>
      {!compact && <h2 className="text-xl font-semibold mb-4">Customer Signup</h2>}
      <form onSubmit={onSubmit} className="space-y-3">
        <input className="w-full border rounded p-2" placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
        <input className="w-full border rounded p-2" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} />
        <input className="w-full border rounded p-2" placeholder="Phone (optional)" value={phone} onChange={e => setPhone(e.target.value)} />
        <input className="w-full border rounded p-2" type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
        {error && <div className="text-red-600 text-sm">{error}</div>}
        {success && <div className="text-green-700 text-sm">{success}</div>}
        <button className="w-full bg-gray-900 text-white rounded p-2">Sign up</button>
      </form>
    </div>
  )
}

