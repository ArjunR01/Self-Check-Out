import { useEffect, useState } from 'react'
import api from '../../lib/api'
import { formatINR } from '../../utils/format'

interface Invoice { id: number, code: string, total: number, date: string, status: string }

export function CustomerHistory() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const { data } = await api.get('/customers/me/invoices')
      setInvoices(data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load history')
    }
  }

  useEffect(() => { load() }, [])

  const downloadPdf = async (id: number, code: string) => {
    try {
      const res = await api.get(`/invoices/${id}/pdf`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `invoice_${code}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to download PDF')
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h2 className="text-xl font-semibold mb-4">Invoice History</h2>
      {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
      <div className="bg-white rounded shadow">
        <table className="w-full">
          <thead>
            <tr className="text-left border-b">
              <th className="p-2">Code</th>
              <th className="p-2">Date</th>
              <th className="p-2">Total</th>
              <th className="p-2">Status</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(inv => (
              <tr key={inv.id} className="border-b">
                <td className="p-2 font-mono">{inv.code}</td>
                <td className="p-2">{new Date(inv.date).toLocaleString('en-IN')}</td>
                <td className="p-2">{formatINR(inv.total)}</td>
                <td className="p-2">{inv.status}</td>
                <td className="p-2">
                  <button onClick={() => downloadPdf(inv.id, inv.code)} className="px-3 py-1 bg-gray-100 rounded hover:bg-gray-200">PDF</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

