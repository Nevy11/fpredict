import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/backtest')({
  component: Backtest,
})

function Backtest() {
  return (
    <div className="container">
      <h1 className="heading-primary">Backtest Simulator</h1>
      <p className="subtitle">Run the FPredict Engine against historical EPL seasons to evaluate model Alpha.</p>

      <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', textAlign: 'center' }}>
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--accent-cyan)" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" style={{ marginBottom: '1.5rem' }}>
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
        </svg>
        <h2 className="heading-secondary" style={{ fontSize: '2rem' }}>Simulator Offline</h2>
        <p style={{ color: 'var(--text-muted)', maxWidth: '500px', fontSize: '1.1rem' }}>
          The backtesting module is currently being calibrated with the latest 2025/26 season data warehouse. Check back later to run simulations.
        </p>
        <button className="btn-primary" style={{ marginTop: '2rem', maxWidth: '300px', opacity: 0.5, cursor: 'not-allowed' }} disabled>
          Initialize Backtest
        </button>
      </div>
    </div>
  )
}
