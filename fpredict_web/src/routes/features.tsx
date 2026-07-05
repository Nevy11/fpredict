import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { ClientOnly } from '../components/ClientOnly'
import { MomentumChart } from '../components/MomentumChart'
import { fetchFeatureSeries, fetchTeams, type FeatureSeries } from '../lib/api'

export const Route = createFileRoute('/features')({
  ssr: false,
  component: Features,
})

const FALLBACK_TEAMS = ['Manchester City', 'Arsenal', 'Liverpool', 'Chelsea']

function Features() {
  const [teams, setTeams] = useState<string[]>(FALLBACK_TEAMS)
  const [team, setTeam] = useState('Manchester City')
  const [series, setSeries] = useState<FeatureSeries | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTeams()
      .then((loadedTeams) => {
        if (loadedTeams.length > 0) {
          setTeams(loadedTeams)
        }
      })
      .catch(() => {
        // Keep fallback list when API is offline.
      })
  }, [])

  useEffect(() => {
    setLoading(true)
    setError('')

    fetchFeatureSeries(team)
      .then(setSeries)
      .catch((err: Error) => {
        setSeries(null)
        setError(err.message || 'Unable to load feature data.')
      })
      .finally(() => setLoading(false))
  }, [team])

  return (
    <div className="container page-stack">
      <header className="page-header">
        <h1 className="heading-primary">Feature Store Metrics</h1>
        <p className="subtitle">
          Track Elo momentum, squad degradation, and sentiment volatility across the season.
        </p>
      </header>

      <div className="glass-card card-stack">
        <div className="card-toolbar">
          <div>
            <h2 className="heading-secondary card-title">Momentum vs Squad Degradation</h2>
            <p className="card-caption">Dual-axis view of team strength and injury-adjusted SDI.</p>
          </div>
          <select
            className="glass-input compact-input"
            value={team}
            onChange={(event) => setTeam(event.target.value)}
          >
            {teams.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>

        {loading && <div className="status-banner">Loading feature snapshots...</div>}
        {!loading && error && <div className="status-banner error">{error}</div>}

        {!loading && series && (
          <>
            <ClientOnly fallback={<div className="chart-placeholder">Preparing chart...</div>}>
              <MomentumChart data={series.snapshots} />
            </ClientOnly>

            <div className="stat-grid">
              <div className="stat-card">
                <div className="stat-label">Avg Elo Rating</div>
                <div className="stat-value">{series.summary.avg_elo.toFixed(1)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Latest SDI</div>
                <div className="stat-value accent-cyan">{series.summary.latest_sdi.toFixed(2)}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Market Overround</div>
                <div className="stat-value accent-cyan">{series.summary.market_overround.toFixed(1)}%</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Sentiment Volatility</div>
                <div className="stat-value accent-purple">{series.summary.sentiment_volatility}</div>
              </div>
            </div>

            <div className="feature-table-wrap">
              <h3 className="section-title">Recent Snapshots</h3>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Elo</th>
                    <th>SDI</th>
                    <th>Form</th>
                    <th>Sentiment</th>
                  </tr>
                </thead>
                <tbody>
                  {series.snapshots.slice(-6).reverse().map((snapshot) => (
                    <tr key={snapshot.date}>
                      <td>{snapshot.date}</td>
                      <td>{snapshot.elo.toFixed(0)}</td>
                      <td>{snapshot.sdi.toFixed(2)}</td>
                      <td>{snapshot.form.toFixed(2)}</td>
                      <td>{snapshot.sentiment.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
