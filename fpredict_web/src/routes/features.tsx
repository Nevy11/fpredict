import { createFileRoute } from '@tanstack/react-router'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useState } from 'react'

export const Route = createFileRoute('/features')({
  component: Features,
})

const MOCK_MOMENTUM_DATA = [
  { match: 'GW1', elo: 1500, sdi: 1.0 },
  { match: 'GW2', elo: 1515, sdi: 0.98 },
  { match: 'GW3', elo: 1522, sdi: 0.95 },
  { match: 'GW4', elo: 1510, sdi: 0.97 },
  { match: 'GW5', elo: 1495, sdi: 0.92 },
  { match: 'GW6', elo: 1505, sdi: 0.94 },
  { match: 'GW7', elo: 1520, sdi: 0.90 },
  { match: 'GW8', elo: 1535, sdi: 0.88 },
  { match: 'GW9', elo: 1542, sdi: 0.85 },
  { match: 'GW10', elo: 1555, sdi: 0.82 },
]

function Features() {
  const [team, setTeam] = useState('Manchester City')

  return (
    <div className="container" style={{ width: '100%' }}>
      <h1 className="heading-primary">Feature Store Metrics</h1>
      <p className="subtitle">Interactive visualization of Dynamic State Vectors across the season.</p>

      <div className="glass-card" style={{ minHeight: '60vh' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
          <h2 className="heading-secondary" style={{ margin: 0 }}>Momentum vs Squad Degradation (SDI)</h2>
          <select className="glass-input" style={{ padding: '0.5rem 1rem' }} value={team} onChange={(e) => setTeam(e.target.value)}>
            <option>Manchester City</option>
            <option>Arsenal</option>
            <option>Liverpool</option>
          </select>
        </div>

        {/* Recharts Area Chart */}
        <div style={{ height: '400px', width: '100%', marginBottom: '2rem' }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={MOCK_MOMENTUM_DATA} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorElo" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f0ff" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#00f0ff" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="colorSdi" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8a2be2" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#8a2be2" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="match" stroke="#8b949e" />
              <YAxis yAxisId="left" stroke="#00f0ff" domain={['dataMin - 20', 'dataMax + 20']} />
              <YAxis yAxisId="right" orientation="right" stroke="#8a2be2" domain={[0, 1.2]} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'rgba(10, 12, 16, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '8px' }} 
                itemStyle={{ color: '#fff' }}
              />
              <Legend />
              <Area yAxisId="left" type="monotone" dataKey="elo" name="Elo Rating" stroke="#00f0ff" fillOpacity={1} fill="url(#colorElo)" />
              <Area yAxisId="right" type="monotone" dataKey="sdi" name="SDI Multiplier" stroke="#8a2be2" fillOpacity={1} fill="url(#colorSdi)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
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

