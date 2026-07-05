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
  const [predictionData, setPredictionData] = useState<any>(null)
  const [isPredicting, setIsPredicting] = useState(false)

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault()
    if (homeTeam === awayTeam) {
      alert("Home and Away teams must be different!")
      return
    }
    
    setIsPredicting(true)
    
    try {
      const response = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          home_team: homeTeam,
          away_team: awayTeam
        })
      });
      
      if (!response.ok) {
        throw new Error("Failed to fetch prediction");
      }
      
      const data = await response.json();
      setPredictionData(data);
    } catch (error) {
      console.error(error);
      alert("Error fetching prediction");
    } finally {
      setIsPredicting(false);
    }
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

            <button type="submit" className="btn-primary" style={{ marginTop: '1.5rem' }} disabled={isPredicting}>
              {isPredicting ? 'Calculating Probabilities...' : 'Run Prediction Engine'}
            </button>
          </form>

          {predictionData && !isPredicting && (
            <div className="prediction-results" style={{ marginTop: '2rem' }}>
              <h3 style={{ marginBottom: '1.5rem', color: '#fff' }}>Ensemble Probabilities</h3>
              
              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Home Win ({homeTeam})</span>
                  <span className="prob-value">{predictionData.home.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${predictionData.home}%` }}></div>
                </div>
              </div>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Draw</span>
                  <span className="prob-value">{predictionData.draw.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${predictionData.draw}%`, background: '#8b949e' }}></div>
                </div>
              </div>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Away Win ({awayTeam})</span>
                  <span className="prob-value">{predictionData.away.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${predictionData.away}%`, background: 'linear-gradient(90deg, #8a2be2, #0047ff)' }}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Deep Dive or Schedule */}
        <div className="glass-card">
          {!predictionData || isPredicting ? (
            <>
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
            </>
          ) : (
            <div className="deep-dive-results" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <h2 className="heading-secondary">Quantum Model Deep Dive</h2>
              
              {/* Value Bets */}
              {predictionData.value_bets && predictionData.value_bets.length > 0 && (
                <div style={{ padding: '1rem', background: 'rgba(0, 255, 128, 0.1)', border: '1px solid #00ff80', borderRadius: '8px' }}>
                  <h4 style={{ color: '#00ff80', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    🔥 Value Bet Detected
                  </h4>
                  {predictionData.value_bets.map((bet: any, i: number) => (
                    <div key={i} style={{ color: '#fff', fontSize: '0.95rem' }}>
                      <strong>{bet.pick}</strong> represents positive EV.<br />
                      Recommended Bankroll Stake: <strong>{(bet.kelly * 100).toFixed(2)}%</strong> (Fractional Kelly)
                    </div>
                  ))}
                </div>
              )}

              {/* Bookmaker Odds Comparison */}
              <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <h4 style={{ color: '#00d4ff', marginBottom: '1rem' }}>Market Bookmaker Odds</h4>
                <div style={{ display: 'flex', justifyContent: 'space-between', color: '#ccc', fontSize: '0.95rem' }}>
                  <div>{homeTeam}: <strong style={{color:'#fff'}}>{predictionData.odds[0].toFixed(2)}</strong></div>
                  <div>Draw: <strong style={{color:'#fff'}}>{predictionData.odds[1].toFixed(2)}</strong></div>
                  <div>{awayTeam}: <strong style={{color:'#fff'}}>{predictionData.odds[2].toFixed(2)}</strong></div>
                </div>
              </div>
              
              {/* Features Breakdown */}
              <div>
                <h4 style={{ color: '#b3b3b3', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Model Features (State Vectors)</h4>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', fontSize: '0.85rem', color: '#aaa' }}>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '6px' }}>
                    <strong style={{color:'#fff', display: 'block', marginBottom: '0.5rem'}}>{homeTeam}</strong>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Elo:</span> <span>{predictionData.home_features.elo.toFixed(0)}</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>SDI:</span> <span>{predictionData.home_features.sdi.toFixed(2)}</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Form (PPG):</span> <span>{predictionData.home_features.form.toFixed(2)}</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Sentiment:</span> <span>{predictionData.home_features.sent.toFixed(2)}</span></div>
                  </div>
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.75rem', borderRadius: '6px' }}>
                    <strong style={{color:'#fff', display: 'block', marginBottom: '0.5rem'}}>{awayTeam}</strong>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Elo:</span> <span>{predictionData.away_features.elo.toFixed(0)}</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>SDI:</span> <span>{predictionData.away_features.sdi.toFixed(2)}</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Form (PPG):</span> <span>{predictionData.away_features.form.toFixed(2)}</span></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Sentiment:</span> <span>{predictionData.away_features.sent.toFixed(2)}</span></div>
                  </div>
                </div>
              </div>

              {/* Historical Matches */}
              {predictionData.historical_matches && predictionData.historical_matches.length > 0 && (
                <div>
                  <h4 style={{ color: '#b3b3b3', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>Recent H2H Matchups</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                    {predictionData.historical_matches.map((m: any, i: number) => (
                      <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '0.85rem', color: '#ccc' }}>
                        <span style={{ color: '#888' }}>{m.date}</span>
                        <span style={{ fontWeight: '500' }}>
                          {m.home_team} <strong style={{ color: '#fff', margin: '0 0.5rem' }}>{m.home_goals} - {m.away_goals}</strong> {m.away_team}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
