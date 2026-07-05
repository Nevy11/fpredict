import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'

export const Route = createFileRoute('/')({
  component: Index,
})

const TEAMS = [
  "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton & Hove Albion", 
  "Chelsea", "Coventry City", "Crystal Palace", "Everton", "Fulham", 
  "Hull City", "Ipswich Town", "Leeds United", "Liverpool", "Manchester City", 
  "Manchester United", "Newcastle United", "Nottingham Forest", "Sunderland", "Tottenham Hotspur"
]

const MOCK_SCHEDULE = [
  { home: "Manchester City", away: "Arsenal", date: "Aug 21, 2026", time: "20:00 BST" },
  { home: "Coventry City", away: "Chelsea", date: "Aug 22, 2026", time: "12:30 BST" },
  { home: "Liverpool", away: "Aston Villa", date: "Aug 22, 2026", time: "15:00 BST" },
  { home: "Sunderland", away: "Newcastle United", date: "Aug 22, 2026", time: "15:00 BST" },
  { home: "Tottenham Hotspur", away: "Everton", date: "Aug 22, 2026", time: "17:30 BST" },
  { home: "Manchester United", away: "Leeds United", date: "Aug 23, 2026", time: "14:00 BST" },
  { home: "Hull City", away: "Ipswich Town", date: "Aug 23, 2026", time: "16:30 BST" },
  { home: "Brighton & Hove Albion", away: "Bournemouth", date: "Aug 24, 2026", time: "20:00 BST" },
]

function Index() {
  const [homeTeam, setHomeTeam] = useState('Manchester City')
  const [awayTeam, setAwayTeam] = useState('Arsenal')
  const [prediction, setPrediction] = useState<{ home: number, draw: number, away: number } | null>(null)
  const [isPredicting, setIsPredicting] = useState(false)

  const handlePredict = (e: React.FormEvent) => {
    e.preventDefault()
    if (homeTeam === awayTeam) {
      alert("Home and Away teams must be different!")
      return
    }
    
    setIsPredicting(true)
    // Simulate API call to the Python Two-Tower ensemble
    setTimeout(() => {
      // Mocked calculation based on team names to make it seem dynamic
      const hash = homeTeam.length * awayTeam.length
      const baseHome = 40 + (hash % 30)
      const baseDraw = 20 + (hash % 15)
      const baseAway = 100 - baseHome - baseDraw
      
      setPrediction({
        home: baseHome,
        draw: baseDraw,
        away: baseAway
      })
      setIsPredicting(false)
    }, 1200)
  }

  return (
    <div className="container">
      <h1 className="heading-primary">FPredict Engine</h1>
      <p className="subtitle">Quantum-driven predictive modeling for the 2026/27 Premier League Season.</p>

      <div className="grid-2">
        {/* Left Column: Prediction Interface */}
        <div className="glass-card">
          <h2 className="heading-secondary">Match Predictor</h2>
          <form onSubmit={handlePredict}>
            <div className="input-group">
              <label className="input-label">Home Team</label>
              <select 
                className="glass-input" 
                value={homeTeam} 
                onChange={(e) => setHomeTeam(e.target.value)}
              >
                {TEAMS.map(team => (
                  <option key={team} value={team}>{team}</option>
                ))}
              </select>
            </div>
            
            <div className="input-group">
              <label className="input-label">Away Team</label>
              <select 
                className="glass-input" 
                value={awayTeam} 
                onChange={(e) => setAwayTeam(e.target.value)}
              >
                {TEAMS.map(team => (
                  <option key={team} value={team}>{team}</option>
                ))}
              </select>
            </div>

            <button type="submit" className="btn-primary" disabled={isPredicting}>
              {isPredicting ? 'Calculating Probabilities...' : 'Run Prediction Engine'}
            </button>
          </form>

          {prediction && !isPredicting && (
            <div className="prediction-results">
              <h3 style={{ marginBottom: '1.5rem', color: '#fff' }}>Ensemble Probabilities</h3>
              
              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Home Win ({homeTeam})</span>
                  <span className="prob-value">{prediction.home.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${prediction.home}%` }}></div>
                </div>
              </div>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Draw</span>
                  <span className="prob-value">{prediction.draw.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${prediction.draw}%`, background: '#8b949e' }}></div>
                </div>
              </div>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Away Win ({awayTeam})</span>
                  <span className="prob-value">{prediction.away.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${prediction.away}%`, background: 'linear-gradient(90deg, #8a2be2, #0047ff)' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Next Season Schedule */}
        <div className="glass-card">
          <h2 className="heading-secondary">2026/27 Opening Fixtures</h2>
          <div className="schedule-list">
            {MOCK_SCHEDULE.map((match, i) => (
              <div className="match-item" key={i}>
                <div className="team-name home">{match.home}</div>
                <div className="vs-container">
                  <span className="vs">VS</span>
                  <span className="match-time">{match.date} &bull; {match.time}</span>
                </div>
                <div className="team-name away">{match.away}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
