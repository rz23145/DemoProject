"use client"

import { useEffect, useState } from "react"

export default function Home() {
  const [briefing, setBriefing] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    const fetchBriefing = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
        const res = await fetch(`${apiUrl}/api/briefing/latest`)
        const data = await res.json()

        if (data.error) {
          setError(data.error)
        } else {
          setBriefing(data)
        }
      } catch (e) {
        setError(String(e))
      } finally {
        setLoading(false)
      }
    }

    fetchBriefing()
  }, [])

  if (loading) return <div className="p-8 text-center text-gray-500">Loading market data...</div>
  if (error) return <div className="p-8 text-red-600">Error: {error}</div>
  if (!briefing) return <div className="p-8 text-gray-500">No briefing available</div>

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 bg-white">
      <div className="border-l-4 border-blue-600 pl-6 py-4">
        <h1 className="text-5xl font-bold text-gray-900">Market Intelligence Brief</h1>
        <p className="text-gray-500 text-sm mt-2">Week ending {briefing.week_ending}</p>
        <p className="text-gray-600 mt-4 text-lg leading-relaxed">{briefing.executive_summary}</p>
      </div>

      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">What Moved This Week</h2>
        <div className="grid gap-3">
          {briefing.market_signals?.map((signal: any, i: number) => (
            <div key={i} className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-semibold text-gray-900">{signal.signal}</p>
                  <p className="text-sm text-gray-600 mt-1">{signal.why}</p>
                </div>
                <span className={`text-xs font-bold px-3 py-1 rounded ${
                  signal.magnitude === "High" ? "bg-red-100 text-red-700" :
                  signal.magnitude === "Medium" ? "bg-yellow-100 text-yellow-700" :
                  "bg-green-100 text-green-700"
                }`}>
                  {signal.magnitude}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Trends & Private Market Impact</h2>
        <div className="grid gap-4">
          {briefing.key_trends?.map((trend: any, i: number) => (
            <div key={i} className={`border-l-4 p-5 rounded-r-lg ${
              trend.direction === "tailwind" ? "border-green-500 bg-green-50" : "border-red-500 bg-red-50"
            }`}>
              <div className="flex justify-between items-start mb-3">
                <h3 className="font-bold text-lg text-gray-900">{trend.name}</h3>
                <span className={`text-xs font-bold px-3 py-1 rounded ${
                  trend.direction === "tailwind" ? "bg-green-200 text-green-800" : "bg-red-200 text-red-800"
                }`}>
                  {trend.direction === "tailwind" ? "✓ Tailwind" : "⚠ Headwind"}
                </span>
              </div>

              <div className="space-y-2 text-sm">
                <p className="text-gray-600"><strong>What moved:</strong> {trend.what_moved}</p>
                <p className="text-gray-600"><strong>For private markets:</strong> {trend.private_market_impact}</p>
                <p className="text-gray-600"><strong>Affected sectors:</strong> {trend.affected_sectors?.join(", ")}</p>
                <p className="text-gray-600"><strong>Timeline:</strong> {trend.timeline}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="p-5 rounded-lg border border-green-200 bg-green-50">
          <h3 className="font-bold text-lg text-green-900 mb-3">Tailwinds (Opportunities)</h3>
          <ul className="space-y-2">
            {briefing.portfolio_implications?.tailwinds?.map((item: string, i: number) => (
              <li key={i} className="text-sm text-green-800">→ {item}</li>
            ))}
          </ul>
        </div>

        <div className="p-5 rounded-lg border border-red-200 bg-red-50">
          <h3 className="font-bold text-lg text-red-900 mb-3">Headwinds (Risks)</h3>
          <ul className="space-y-2">
            {briefing.portfolio_implications?.headwinds?.map((item: string, i: number) => (
              <li key={i} className="text-sm text-red-800">→ {item}</li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Deal Sourcing Angles (Act Now)</h2>
        <div className="grid gap-4">
          {briefing.sourcing_angles?.map((angle: any, i: number) => (
            <div key={i} className="p-5 rounded-lg border-2 border-blue-400 bg-blue-50">
              <h3 className="font-bold text-lg text-blue-900">{angle.angle}</h3>
              <p className="text-sm text-gray-700 mt-2">{angle.opportunity}</p>
              <div className="mt-3 space-y-1">
                <p className="text-sm"><strong>Target:</strong> {angle.which_founders}</p>
                <p className="text-sm"><strong>Urgency:</strong> <span className="text-red-600 font-bold">{angle.urgency}</span></p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="pt-6 border-t border-gray-200 text-center text-xs text-gray-500">
        <p>Generated: {new Date(briefing.generated_at).toLocaleString()}</p>
        <p>Data sources: {briefing.data_sources?.join(", ")}</p>
      </div>
    </div>
  )
}
