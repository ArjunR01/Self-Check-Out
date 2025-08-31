import { useRef, useState } from 'react'
import api from '../../lib/api'
import { formatINR } from '../../utils/format'

export function OfficialFetchBill() {
  const [code, setCode] = useState('')
  const [bill, setBill] = useState<any | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)
  const scannerRef = useRef<HTMLDivElement | null>(null)
  const scannerInstanceRef = useRef<any>(null)

  async function fetchBill(c: string) {
    setError(null)
    setBill(null)
    try {
      const res = await api.get(`/invoices/by-code/${encodeURIComponent(c.trim())}`)
      setBill(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Bill not found')
    }
  }

  async function startScanner() {
    setError(null)
    try {
      const { Html5Qrcode } = await import('html5-qrcode')
      const id = 'qr-reader-official'
      if (!scannerRef.current) return
      scannerRef.current.innerHTML = ''
      const div = document.createElement('div')
      div.id = id
      scannerRef.current.appendChild(div)
      const h5 = new Html5Qrcode(id)
      scannerInstanceRef.current = h5
      await h5.start({ facingMode: 'environment' }, { fps: 10, qrbox: 250 }, (decodedText: string) => {
        fetchBill(decodedText)
      })
      setScanning(true)
    } catch (e: any) {
      setError('Failed to start camera scanner. You can still type the bill code.')
    }
  }

  async function stopScanner() {
    try {
      await scannerInstanceRef.current?.stop()
      await scannerInstanceRef.current?.clear()
    } catch {}
    setScanning(false)
  }

  async function markPaid() {
    if (!bill) return
    try {
      const res = await api.post(`/invoices/${bill.id}/pay`)
      setBill(res.data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to mark paid')
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Fetch Bill</h2>
      <div className="flex gap-2">
        <input className="border rounded p-2 flex-1" placeholder="Bill code" value={code} onChange={e => setCode(e.target.value)} />
        <button className="bg-purple-700 text-white px-4 py-2 rounded" onClick={() => fetchBill(code)}>Fetch</button>
        {!scanning ? (
          <button className="bg-gray-900 text-white px-4 py-2 rounded" onClick={startScanner}>Start Scanner</button>
        ) : (
          <button className="bg-gray-600 text-white px-4 py-2 rounded" onClick={stopScanner}>Stop Scanner</button>
        )}
      </div>
      {error && <div className="text-red-600 mt-2">{error}</div>}
      <div ref={scannerRef} className="mt-4" />

      {bill && (
        <div className="mt-6 border rounded p-4 bg-white">
          <div className="text-sm text-gray-600">Customer</div>
          <div className="font-semibold">{bill.customer_name}</div>
          <div className="mt-2">Status: <span className="uppercase font-semibold">{bill.status}</span></div>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr className="text-left text-sm border-b">
                  <th className="p-2">Product</th><th className="p-2">Qty</th><th className="p-2">Subtotal</th><th className="p-2">Net Wt</th>
                </tr>
              </thead>
              <tbody>
                {bill.items.map((it: any) => (
                  <tr key={it.id} className="border-b text-sm">
                    <td className="p-2">{it.product_name}</td>
                    <td className="p-2">{it.quantity}</td>
                    <td className="p-2">{formatINR(it.subtotal)}</td>
                    <td className="p-2">{it.net_weight.toFixed(3)} kg</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-sm">Total: <span className="font-semibold">{formatINR(bill.total)}</span> | Net Weight: <span className="font-semibold">{(bill.total_weight || 0).toFixed(3)} kg</span></div>
          {bill.status !== 'paid' && (
            <button className="mt-4 bg-green-600 text-white px-4 py-2 rounded" onClick={markPaid}>Mark as Paid</button>
          )}
        </div>
      )}
    </div>
  )
}

