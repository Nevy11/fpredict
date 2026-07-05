import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { ClientOnly } from '../components/ClientOnly'
import { EquityChart } from '../components/EquityChart'
import { runBacktest, type BacktestResult } from '../lib/api'

export const Route = createFileRoute('/backtest')({
  ssr: false,
  component: Backtest,
})

const SEASONS = ['2023/24', '2024/25']

function readSetting(key: string, fallback: number) {
  if (typeof window === 'undefined') {
    return fallback
  }
  const saved = window.localStorage.getItem(key)
  return saved ? parseFloat(saved) : fallback
}

function Backtest() {
  const [season, setSeason] = useState(SEASONS[0])
  const [bankroll, setBankroll] = useState(() => readSetting('fpredict_base_bankroll', 1000))
  const [kellyFraction, setKellyFraction] = useState(() => readSetting('fpredict_kelly_fraction', 0.5))
  const [result, setResult] = useState<BacktestResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleRun = async () => {
    setLoading(true)
    setError('')

    try {
      const report = await runBacktest({
        season,
        initial_bankroll: bankroll,
        kelly_fraction: kellyFraction,
      })
      setResult(report)
    } catch (err) {
      setResult(null)
      setError(err instanceof Error ? err.message : 'Backtest failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container page-stack">
      <header className="page-header">
        <h1 className="heading-primary">Backtest Simulator</h1>
        <p className="subtitle">
          Replay historical EPL fixtures with Kelly-sized stakes and measure model alpha.
        </p>
      </header>

      <div className="grid-2 backtest-grid">
        <div className="glass-card card-stack">
          <h2 className="heading-secondary card-title">Simulation Controls</h2>

          <div className="input-group">
            <label className="input-label">Season</label>
            <select
              className="glass-input"
              value={season}
              onChange={(event) => setSeason(event.target.value)}
            >
              {SEASONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <div className="input-group">
            <label className="input-label">Starting Bankroll ($)</label>
            <input
              type="number"
              className="glass-input"
              value={bankroll}
              min={100}
              step={100}
              onChange={(event) => setBankroll(parseFloat(event.target.value) || 0)}
            />
          </div>

          <div className="input-group">
            <div className="range-header">
              <label className="input-label">Kelly Multiplier</label>
              <span className="range-value">{kellyFraction.toFixed(1)}x</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.1"
              value={kellyFraction}
              onChange={(event) => setKellyFraction(parseFloat(event.target.value))}
              className="range-input cyan"
            />
          </div>

          <button className="btn-primary" onClick={handleRun} disabled={loading || bankroll <= 0}>
            {loading ? 'Running Simulation...' : 'Initialize Backtest'}
          </button>

          {error && <div className="status-banner error">{error}</div>}
        </div>

        <div className="glass-card card-stack">
          {!result ? (
            <div className="empty-state">
              <div className="empty-icon">↗</div>
              <h2 className="heading-secondary">Ready to Simulate</h2>
              <p>
                Choose a season and bankroll, then run the engine against historical odds and outcomes.
              </p>
            </div>
          ) : (
            <>
              <div className="stat-grid compact">
                <div className="stat-card">
                  <div className="stat-label">Final Bankroll</div>
                  <div className="stat-value accent-green">${result.final_bankroll.toFixed(2)}</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">ROI</div>
                  <div className={`stat-value ${result.roi >= 0 ? 'accent-green' : 'accent-red'}`}>
                    {result.roi >= 0 ? '+' : ''}
                    {result.roi.toFixed(2)}%
                  </div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Win Rate</div>
                  <div className="stat-value">{result.win_rate.toFixed(1)}%</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Total Bets</div>
                  <div className="stat-value">{result.total_bets}</div>
                </div>
              </div>

              <ClientOnly fallback={<div className="chart-placeholder">Preparing equity curve...</div>}>
                <EquityChart data={result.equity_curve} />
              </ClientOnly>

              <div className="feature-table-wrap">
                <h3 className="section-title">Recent Trades</h3>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Match</th>
                      <th>Pick</th>
                      <th>Result</th>
                      <th>Bankroll</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.recent_bets.map((bet, index) => (
                      <tr key={`${bet.date}-${index}`}>
                        <td>{bet.date}</td>
                        <td>{bet.match}</td>
                        <td>{bet.pick}</td>
                        <td className={bet.won ? 'accent-green' : 'accent-red'}>
                          {bet.won ? 'Win' : 'Loss'}
                        </td>
                        <td>${bet.bankroll.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
