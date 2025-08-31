import { useEffect, useRef, useState } from 'react'
import api from '../../lib/api'
import { formatINR } from '../../utils/format'

function getLocalCart() {
  const raw = localStorage.getItem('abs_cart')
  return raw ? JSON.parse(raw) as Array<{ code: string; name: string; price_per_unit: number; weight_per_unit: number; quantity: number }> : []
}
function setLocalCart(data: any) {
  localStorage.setItem('abs_cart', JSON.stringify(data))
}

export function CustomerScan() {
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [cart, setCart] = useState(getLocalCart())
  const [scanning, setScanning] = useState(false)
  const scannerRef = useRef<HTMLDivElement | null>(null)
  const scannerInstanceRef = useRef<any>(null)

  useEffect(() => {
    setLocalCart(cart)
  }, [cart])

  async function addCode(c: string) {
    const trimmed = c.trim()
    if (!trimmed) return
    setError(null)
    try {
      const res = await api.get(`/products/${encodeURIComponent(trimmed)}`)
      const p = res.data as { code: string; name: string; price_per_unit: number; weight_per_unit: number }
      setCart(prev => {
        const idx = prev.findIndex(x => x.code === p.code)
        if (idx >= 0) {
          const copy = [...prev]
          copy[idx] = { ...copy[idx], quantity: copy[idx].quantity + 1 }
          return copy
        }
        return [...prev, { code: p.code, name: p.name, price_per_unit: p.price_per_unit, weight_per_unit: p.weight_per_unit, quantity: 1 }]
      })
      setCode('')
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid Product')
    }
  }

  async function startScanner() {
    setError(null)
    try {
      const { Html5Qrcode } = await import('html5-qrcode')
      const id = 'qr-reader'
      if (!scannerRef.current) return
      scannerRef.current.innerHTML = ''
      const div = document.createElement('div')
      div.id = id
      scannerRef.current.appendChild(div)
      const h5 = new Html5Qrcode(id)
      scannerInstanceRef.current = h5
      await h5.start({ facingMode: 'environment' }, { fps: 10, qrbox: 250 }, (decodedText: string) => {
        // treat decodedText as product code
        addCode(decodedText)
      })
      setScanning(true)
    } catch (e: any) {
      setError('Failed to start camera scanner. You can still use manual entry.')
    }
  }

  async function stopScanner() {
    try {
      await scannerInstanceRef.current?.stop()
      await scannerInstanceRef.current?.clear()
    } catch {}
    setScanning(false)
  }

  const total = cart.reduce((a, b) => a + b.price_per_unit * b.quantity, 0)
  const totalWeight = cart.reduce((a, b) => a + b.weight_per_unit * b.quantity, 0)

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Scan or Enter Product Code</h2>
      <div className="flex gap-2">
        <input className="border rounded p-2 flex-1" placeholder="Enter code (e.g. P1001)" value={code} onChange={e => setCode(e.target.value)} />
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={() => addCode(code)}>Add</button>
        {!scanning ? (
          <button className="bg-gray-900 text-white px-4 py-2 rounded" onClick={startScanner}>Start Scanner</button>
        ) : (
          <button className="bg-gray-600 text-white px-4 py-2 rounded" onClick={stopScanner}>Stop Scanner</button>
        )}
      </div>
      {error && <div className="text-red-600 mt-2">{error}</div>}
      <div ref={scannerRef} className="mt-4" />

      <div className="mt-6">
        <h3 className="font-semibold mb-2">Cart (local)</h3>
        {cart.length === 0 ? (
          <div className="text-gray-600">No items yet.</div>
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
                    <td className="p-2">{it.quantity}</td>
                    <td className="p-2">{formatINR(it.price_per_unit * it.quantity)}</td>
                    <td className="p-2">{(it.weight_per_unit * it.quantity).toFixed(3)} kg</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-3 text-sm">Total: <span className="font-semibold">{formatINR(total)}</span> | Net Weight: <span className="font-semibold">{totalWeight.toFixed(3)} kg</span></div>
      </div>
    </div>
  )
}

