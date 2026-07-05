import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/features')({
  component: Features,
})

function Features() {
  return (
    <div className="container">
      <h1 className="heading-primary">Feature Store Metrics</h1>
      <p className="subtitle">Real-time visualizations of Dynamic State Vectors across all 20 EPL teams.</p>

      <div className="glass-card" style={{ minHeight: '60vh', position: 'relative', overflow: 'hidden' }}>
        {/* Placeholder for future charts */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h2 className="heading-secondary" style={{ margin: 0 }}>Global SDI Distribution</h2>
          <select className="glass-input" style={{ padding: '0.5rem 1rem' }}>
            <option>Matchweek 1</option>
            <option>Pre-season</option>
          </select>
        </div>

        <div style={{
          height: '300px', 
          width: '100%', 
          background: 'linear-gradient(180deg, rgba(0, 240, 255, 0.1) 0%, rgba(0,0,0,0) 100%)',
          borderBottom: '2px solid var(--accent-cyan)',
          borderLeft: '2px solid rgba(255,255,255,0.1)',
          position: 'relative',
          display: 'flex',
          alignItems: 'flex-end',
          justifyContent: 'space-around',
          padding: '0 2rem'
        }}>
          {/* Mock bars for the chart */}
          {[60, 45, 80, 55, 90, 40, 70, 30].map((height, i) => (
            <div key={i} style={{
              width: '40px',
              height: `${height}%`,
              background: 'linear-gradient(0deg, var(--accent-blue), var(--accent-cyan))',
              borderRadius: '4px 4px 0 0',
              opacity: 0.8,
              transition: 'height 1s ease'
            }}></div>
          ))}
        </div>

        <div style={{ marginTop: '2rem', display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Avg Elo Rating</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#fff', marginTop: '0.5rem' }}>1502.4</div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Market Overround</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent-cyan)', marginTop: '0.5rem' }}>104.2%</div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px' }}>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', textTransform: 'uppercase' }}>Sentiment Volatility</div>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent-purple)', marginTop: '0.5rem' }}>High</div>
          </div>
        </div>
      </div>
    </div>
  )
}
