// import { useMemo, useState } from 'react'
// import api from '../../lib/api'
// import { getTokens } from '../../lib/auth'
// import { CustomerLogin } from './Auth'
// import { formatINR } from '../../utils/format'

// function getLocalCart() {
//   const raw = localStorage.getItem('abs_cart')
//   return raw ? JSON.parse(raw) as Array<{ code: string; name: string; price_per_unit: number; weight_per_unit: number; quantity: number }> : []
// }
// function setLocalCart(data: any) {
//   localStorage.setItem('abs_cart', JSON.stringify(data))
// }

// export function CustomerCart() {
//   const [cart, setCart] = useState(getLocalCart())
//   const [invoice, setInvoice] = useState<{invoice_id:number, qr_code:string, qr_base64:string, total:number, total_net_weight:number} | null>(null)
//   const [error, setError] = useState<string | null>(null)
//   const [showLogin, setShowLogin] = useState(false)
//   const tokens = getTokens()

//   const totals = useMemo(() => {
//     const total = cart.reduce((a, b) => a + b.price_per_unit * b.quantity, 0)
//     const totalWeight = cart.reduce((a, b) => a + b.weight_per_unit * b.quantity, 0)
//     return { total, totalWeight }
//   }, [cart])

//   function updateQty(code: string, qty: number) {
//     setCart(prev => prev.map(it => it.code === code ? { ...it, quantity: Math.max(0, qty) } : it).filter(it => it.quantity > 0))
//   }
//   function clearCart() {
//     setCart([])
//     setLocalCart([])
//     setInvoice(null)
//   }

//   async function generateBill() {
//     setError(null)
//     setInvoice(null)
//     if (!tokens || tokens.role !== 'customer') {
//       setShowLogin(true)
//       return
//     }
//     try {
//       const items = cart.map(it => ({ code: it.code, quantity: it.quantity }))
//       // Attach local cart to server
//       const attach = await api.post('/carts/attach', { items })
//       const cartId = attach.data.cart_id
//       // Checkout to create invoice
//       const res = await api.post(`/carts/${cartId}/checkout`)
//       setInvoice(res.data)
//       // Do not clear cart to allow showing QR summary; user can clear manually
//     } catch (err: any) {
//       setError(err?.response?.data?.detail || 'Failed to generate bill')
//     }
//   }

//   return (
//     <div className="p-6 max-w-3xl mx-auto">
//       <h2 className="text-xl font-semibold mb-4">Cart</h2>
//       {cart.length === 0 ? (
//         <div className="text-gray-600">Your cart is empty. Go to Scan to add products.</div>
//       ) : (
//         <div className="overflow-x-auto">
//           <table className="min-w-full bg-white">
//             <thead>
//               <tr className="text-left text-sm border-b">
//                 <th className="p-2">Code</th><th className="p-2">Product</th><th className="p-2">Qty</th><th className="p-2">Price</th><th className="p-2">Net Wt</th>
//               </tr>
//             </thead>
//             <tbody>
//               {cart.map((it, idx) => (
//                 <tr key={idx} className="border-b text-sm">
//                   <td className="p-2">{it.code}</td>
//                   <td className="p-2">{it.name}</td>
//                   <td className="p-2">
//                     <input type="number" min={0} value={it.quantity} onChange={e => updateQty(it.code, Number(e.target.value))} className="w-20 border rounded p-1" />
//                   </td>
//                   <td className="p-2">{formatINR(it.price_per_unit * it.quantity)}</td>
//                   <td className="p-2">{(it.weight_per_unit * it.quantity).toFixed(3)} kg</td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       )}
//       <div className="mt-3 text-sm">Total: <span className="font-semibold">{formatINR(totals.total)}</span> | Net Weight: <span className="font-semibold">{totals.totalWeight.toFixed(3)} kg</span></div>

//       <div className="mt-4 flex gap-2">
//         <button className="bg-green-600 text-white px-4 py-2 rounded" onClick={generateBill}>Generate Bill QR</button>
//         <button className="bg-gray-200 px-4 py-2 rounded" onClick={clearCart}>Clear Cart</button>
//       </div>

//       {error && <div className="text-red-600 mt-2">{error}</div>}

//       {showLogin && (
//         <div className="mt-6 border rounded p-4 bg-white">
//           <h3 className="font-semibold mb-2">Please login to create and save your bill</h3>
//           <CustomerLogin />
//           <p className="text-sm text-gray-600 mt-2">After logging in, click "Generate Bill QR" again.</p>
//         </div>
//       )}

//       {invoice && (
//         <div className="mt-6 border rounded p-4 bg-white">
//           <h3 className="font-semibold mb-2">Show this QR at checkout</h3>
//           <div className="flex items-center gap-6">
//             <img src={`data:image/png;base64,${invoice.qr_base64}`} alt="Invoice QR" className="border shadow rounded" width={180} height={180} />
//             <div>
//               <div className="text-sm text-gray-600">Invoice Code:</div>
//               <div className="font-mono">{invoice.qr_code}</div>
//               <div className="mt-2 text-sm">Total: <span className="font-semibold">{formatINR(invoice.total)}</span></div>
//               <div className="text-sm">Total Net Weight: <span className="font-semibold">{invoice.total_net_weight.toFixed(3)} kg</span></div>
//               <a className="text-blue-600 underline block mt-2" href={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/invoices/${invoice.invoice_id}/qr`} target="_blank" rel="noreferrer">Open QR image</a>
//             </div>
//           </div>
//         </div>
//       )}
//     </div>
//   )
// }

// function useEffect(arg0: () => void, arg1: never[]) {
//   throw new Error('Function not implemented.')
// }



import { useMemo, useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../../lib/api'
import { getTokens } from '../../lib/auth'
import { CustomerLogin } from './Auth'
import { formatINR } from '../../utils/format'

function getLocalCart() {
  const raw = localStorage.getItem('abs_cart')
  return raw ? JSON.parse(raw) as Array<{ code: string; name: string; price_per_unit: number; weight_per_unit: number; quantity: number }> : []
}
function setLocalCart(data: any) {
  localStorage.setItem('abs_cart', JSON.stringify(data))
}

export function CustomerCart() {
  const navigate = useNavigate()
  const [cart, setCart] = useState(getLocalCart())
  const [invoice, setInvoice] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showLogin, setShowLogin] = useState(false)
  const tokens = getTokens()

  // Poll interval ref so we can clear it
  const pollRef = useRef<number | null>(null)

  const totals = useMemo(() => {
    const total = cart.reduce((a, b) => a + b.price_per_unit * b.quantity, 0)
    const totalWeight = cart.reduce((a, b) => a + b.weight_per_unit * b.quantity, 0)
    return { total, totalWeight }
  }, [cart])

  function updateQty(code: string, qty: number) {
    setCart(prev => {
      const next = prev.map(it => it.code === code ? { ...it, quantity: Math.max(0, qty) } : it).filter(it => it.quantity > 0)
      setLocalCart(next)
      return next
    })
  }
  function clearCart() {
    setCart([])
    setLocalCart([])
    setInvoice(null)
  }

  // Stop polling safely
  function stopPolling() {
    if (pollRef.current) {
      window.clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  // Start polling invoice status by id
  function startPolling(invoiceId: number) {
    // stop any existing poll
    stopPolling()

    // poll every 3s
    pollRef.current = window.setInterval(async () => {
      try {
        const res = await api.get(`/invoices/${invoiceId}`)
        const latest = res.data
        // update invoice in UI with latest info
        setInvoice(prev => ({ ...prev, ...latest }))

        if (latest.status === 'paid') {
          // stop polling and handle paid state
          stopPolling()
          // clear local cart and localStorage
          setCart([])
          setLocalCart([])
          // ensure invoice state contains fields our UI expects
          setInvoice(latest)
        }
      } catch (err) {
        // ignore transient errors but log if needed
        console.error('Polling invoice failed', err)
      }
    }, 3000)
  }

  // ensure we cleanup interval when component unmounts
  useEffect(() => {
    return () => {
      stopPolling()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function generateBill() {
    setError(null)
    setInvoice(null)
    if (!tokens || tokens.role !== 'customer') {
      setShowLogin(true)
      return
    }
    try {
      const items = cart.map(it => ({ code: it.code, quantity: it.quantity }))
      // Attach local cart to server
      const attach = await api.post('/carts/attach', { items })
      const cartId = attach.data.cart_id
      // Checkout to create invoice
      const res = await api.post(`/carts/${cartId}/checkout`)
      const created = res.data
      // created should include invoice_id (based on your backend)
      setInvoice(created)

      // Start polling the invoice for status changes (cashier will mark paid)
      // backend returns invoice_id per your earlier code; if backend returns `id`, adapt accordingly
      const invoiceId = created.invoice_id ?? created.id
      if (invoiceId) {
        startPolling(invoiceId)
      } else {
        console.warn('No invoice id returned from checkout; cannot poll status.')
      }
      // Do not clear cart now; will be cleared when invoice becomes paid
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to generate bill')
    }
  }

  // Helper to download PDF or open in new tab
  function openInvoicePdf(id: number, code?: string) {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${base}/invoices/${id}/pdf`
    window.open(url, '_blank')
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Cart</h2>

      {cart.length === 0 ? (
        <div className="text-gray-600">Your cart is empty. Go to Scan to add products.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white">
            <thead>
              <tr className="text-left text-sm border-b">
                <th className="p-2">Code</th><th className="p-2">Product</th><th className="p-2">Qty</th><th className="p-2">Price</th><th className="p-2">Net Wt</th>
              </tr>
            </thead>
            <tbody>
              {cart.map((it, idx) => (
                <tr key={idx} className="border-b text-sm">
                  <td className="p-2">{it.code}</td>
                  <td className="p-2">{it.name}</td>
                  <td className="p-2">
                    <input type="number" min={0} value={it.quantity} onChange={e => updateQty(it.code, Number(e.target.value))} className="w-20 border rounded p-1" />
                  </td>
                  <td className="p-2">{formatINR(it.price_per_unit * it.quantity)}</td>
                  <td className="p-2">{(it.weight_per_unit * it.quantity).toFixed(3)} kg</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-3 text-sm">Total: <span className="font-semibold">{formatINR(totals.total)}</span> | Net Weight: <span className="font-semibold">{totals.totalWeight.toFixed(3)} kg</span></div>

      <div className="mt-4 flex gap-2">
        <button className="bg-green-600 text-white px-4 py-2 rounded" onClick={generateBill}>Generate Bill QR</button>
        <button className="bg-gray-200 px-4 py-2 rounded" onClick={clearCart}>Clear Cart</button>
      </div>

      {error && <div className="text-red-600 mt-2">{error}</div>}

      {showLogin && (
        <div className="mt-6 border rounded p-4 bg-white">
          <h3 className="font-semibold mb-2">Please login to create and save your bill</h3>
          <CustomerLogin onLoginSuccess={() => window.location.reload()} />
          <p className="text-sm text-gray-600 mt-2">After logging in, click "Generate Bill QR" again.</p>
        </div>
      )}

      {invoice && (
        <div className="mt-6 border rounded p-4 bg-white">
          <h3 className="font-semibold mb-2">Show this QR at checkout</h3>
          <div className="flex items-center gap-6">
            {invoice.qr_base64 && (
              <img src={`data:image/png;base64,${invoice.qr_base64}`} alt="Invoice QR" className="border shadow rounded" width={180} height={180} />
            )}
            <div>
              <div className="text-sm text-gray-600">Invoice Code:</div>
              <div className="font-mono">{invoice.qr_code || invoice.code}</div>
              <div className="mt-2 text-sm">Total: <span className="font-semibold">{formatINR(invoice.total)}</span></div>
              <div className="text-sm">Total Net Weight: <span className="font-semibold">{(invoice.total_net_weight ?? invoice.total_weight ?? 0).toFixed(3)} kg</span></div>
              <a className="text-blue-600 underline block mt-2" href={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/invoices/${invoice.invoice_id ?? invoice.id}/qr`} target="_blank" rel="noreferrer">Open QR image</a>
            </div>
          </div>

          {/* Paid acknowledgement UI */}
          {invoice.status === 'paid' ? (
            <div className="mt-6 border-t pt-4 bg-green-50 p-3 rounded">
              <h4 className="font-semibold text-green-700">✅ Payment Confirmed</h4>
              <p className="text-sm text-gray-700 mb-3">Your invoice has been paid by the cashier.</p>
              <div className="flex gap-2">
                <button onClick={() => openInvoicePdf(invoice.invoice_id ?? invoice.id, invoice.qr_code ?? invoice.code)} className="px-3 py-2 bg-gray-800 text-white rounded">Download PDF</button>
                <button onClick={() => window.open(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/invoices/${invoice.invoice_id ?? invoice.id}/pdf`, '_blank')} className="px-3 py-2 bg-blue-600 text-white rounded">View Invoice</button>
                <button onClick={() => { clearCart(); navigate('/customer/scan') }} className="px-3 py-2 bg-green-600 text-white rounded">Scan & Buy Again</button>
              </div>
            </div>
          ) : (
            <div className="mt-4 text-sm text-gray-600">Status: <span className="font-semibold">{invoice.status ?? 'pending'}</span></div>
          )}
        </div>
      )}
    </div>
  )
}


