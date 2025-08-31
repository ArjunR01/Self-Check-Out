import { useEffect, useState } from 'react'
import api from '../../lib/api'
import { formatINR } from '../../utils/format'

interface Daily { date: string, total: number }

export function OfficialDashboard() {
  const [summary, setSummary] = useState<{ total_revenue: number, total_paid_invoices: number, daily_sales: Daily[], top_customers: { customer_id: number, name: string, spent: number }[] } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      const { data } = await api.get('/analytics/summary')
      setSummary(data)
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to load summary')
    }
  }

  useEffect(() => { load() }, [])

  if (error) return <div className="p-6 text-red-600">{error}</div>
  if (!summary) return <div className="p-6">Loading...</div>

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h2 className="text-2xl font-semibold">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded shadow p-4">
          <div className="text-sm text-gray-600">Total Revenue</div>
          <div className="text-2xl font-bold">{formatINR(summary.total_revenue)}</div>
        </div>
        <div className="bg-white rounded shadow p-4">
          <div className="text-sm text-gray-600">Paid Invoices</div>
          <div className="text-2xl font-bold">{summary.total_paid_invoices}</div>
        </div>
      </div>

      <div className="bg-white rounded shadow p-4">
        <h3 className="font-semibold mb-2">Daily Sales</h3>
        <table className="w-full">
          <thead>
            <tr className="text-left border-b">
              <th className="p-2">Date</th>
              <th className="p-2">Total</th>
            </tr>
          </thead>
          <tbody>
            {summary.daily_sales.map(d => (
              <tr key={d.date} className="border-b">
                <td className="p-2">{d.date}</td>
                <td className="p-2">{formatINR(d.total)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="bg-white rounded shadow p-4">
        <h3 className="font-semibold mb-2">Top Customers</h3>
        <table className="w-full">
          <thead>
            <tr className="text-left border-b">
              <th className="p-2">Customer</th>
              <th className="p-2">Total Spent</th>
            </tr>
          </thead>
          <tbody>
            {summary.top_customers.map(c => (
              <tr key={c.customer_id} className="border-b">
                <td className="p-2">{c.name}</td>
                <td className="p-2">{formatINR(c.spent)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

