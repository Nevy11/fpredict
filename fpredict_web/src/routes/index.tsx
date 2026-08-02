import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import { fetchPrediction, fetchTeams, type PredictionResult } from '../lib/api'

type IndexSearch = {
  home?: string
  away?: string
}

export const Route = createFileRoute('/')({
  component: Index,
  validateSearch: (search: Record<string, unknown>): IndexSearch => {
    return {
      home: search.home as string | undefined,
      away: search.away as string | undefined,
    }
  },
})

const FALLBACK_TEAMS = [
  'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton & Hove Albion',
  'Chelsea', 'Coventry City', 'Crystal Palace', 'Everton', 'Fulham',
  'Hull City', 'Ipswich Town', 'Leeds United', 'Liverpool', 'Manchester City',
  'Manchester United', 'Newcastle United', 'Nottingham Forest', 'Sunderland', 'Tottenham Hotspur',
]

const MOCK_SCHEDULE = [
  { home: 'Manchester City', away: 'Arsenal', date: 'Aug 21, 2026', time: '20:00 BST' },
  { home: 'Coventry City', away: 'Chelsea', date: 'Aug 22, 2026', time: '12:30 BST' },
  { home: 'Liverpool', away: 'Aston Villa', date: 'Aug 22, 2026', time: '15:00 BST' },
  { home: 'Sunderland', away: 'Newcastle United', date: 'Aug 22, 2026', time: '15:00 BST' },
  { home: 'Tottenham Hotspur', away: 'Everton', date: 'Aug 22, 2026', time: '17:30 BST' },
  { home: 'Manchester United', away: 'Leeds United', date: 'Aug 23, 2026', time: '14:00 BST' },
  { home: 'Hull City', away: 'Ipswich Town', date: 'Aug 23, 2026', time: '16:30 BST' },
  { home: 'Brighton & Hove Albion', away: 'Bournemouth', date: 'Aug 24, 2026', time: '20:00 BST' },
]

function Index() {
  const { home, away } = Route.useSearch()
  const [teams, setTeams] = useState<string[]>(FALLBACK_TEAMS)
  const [homeTeam, setHomeTeam] = useState(home || 'Manchester City')
  const [awayTeam, setAwayTeam] = useState(away || 'Arsenal')
  const [predictionData, setPredictionData] = useState<PredictionResult | null>(null)
  const [isPredicting, setIsPredicting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTeams()
      .then((loadedTeams) => {
        if (loadedTeams.length > 0) {
          setTeams(loadedTeams)
        }
      })
      .catch(() => {
        // Keep fallback teams when API is offline.
      })
  }, [])

  useEffect(() => {
    if (home) setHomeTeam(home)
    if (away) setAwayTeam(away)
  }, [home, away])

  const handlePredict = async (event: React.FormEvent) => {
    event.preventDefault()
    if (homeTeam === awayTeam) {
      setError('Home and away teams must be different.')
      return
    }

    setIsPredicting(true)
    setError('')

    try {
      const data = await fetchPrediction(homeTeam, awayTeam)
      setPredictionData(data)
    } catch (err) {
      setPredictionData(null)
      setError(err instanceof Error ? err.message : 'Error fetching prediction.')
    } finally {
      setIsPredicting(false)
    }
  }

  const loadFixture = (home: string, away: string) => {
    setHomeTeam(home)
    setAwayTeam(away)
    setPredictionData(null)
    setError('')
  }

  return (
    <div className="container page-stack">
      <header className="page-header">
        <h1 className="heading-primary">FPredict Engine</h1>
        <p className="subtitle">Quantitative predictive modeling for the Premier League season.</p>
      </header>

      <div className="grid-2">
        <div className="glass-card card-stack">
          <h2 className="heading-secondary card-title">Match Predictor</h2>
          <form onSubmit={handlePredict}>
            <div className="input-group">
              <label className="input-label">Home Team</label>
              <select
                className="glass-input"
                value={homeTeam}
                onChange={(event) => setHomeTeam(event.target.value)}
              >
                {teams.map((team) => (
                  <option key={team} value={team}>
                    {team}
                  </option>
                ))}
              </select>
            </div>

            <div className="input-group">
              <label className="input-label">Away Team</label>
              <select
                className="glass-input"
                value={awayTeam}
                onChange={(event) => setAwayTeam(event.target.value)}
              >
                {teams.map((team) => (
                  <option key={team} value={team}>
                    {team}
                  </option>
                ))}
              </select>
            </div>

            <button type="submit" className="btn-primary" disabled={isPredicting}>
              {isPredicting ? 'Calculating Probabilities...' : 'Run Prediction Engine'}
            </button>
          </form>

          {error && <div className="status-banner error">{error}</div>}

          {predictionData && !isPredicting && (
            <div className="prediction-results">
              <h3 className="section-title">Ensemble Probabilities</h3>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Home Win ({homeTeam})</span>
                  <span className="prob-value">{predictionData.home.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div className="prob-fill" style={{ width: `${predictionData.home}%` }} />
                </div>
              </div>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Draw</span>
                  <span className="prob-value">{predictionData.draw.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div
                    className="prob-fill draw"
                    style={{ width: `${predictionData.draw}%` }}
                  />
                </div>
              </div>

              <div className="prob-row">
                <div className="prob-header">
                  <span className="prob-label">Away Win ({awayTeam})</span>
                  <span className="prob-value">{predictionData.away.toFixed(2)}%</span>
                </div>
                <div className="prob-bar">
                  <div
                    className="prob-fill away"
                    style={{ width: `${predictionData.away}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="glass-card card-stack">
          {!predictionData || isPredicting ? (
            <>
              <h2 className="heading-secondary card-title">Opening Fixtures</h2>
              <p className="card-caption">Select a fixture to pre-fill the predictor.</p>
              <div className="schedule-list">
                {MOCK_SCHEDULE.map((match) => (
                  <button
                    type="button"
                    className="match-item match-button"
                    key={`${match.home}-${match.away}`}
                    onClick={() => loadFixture(match.home, match.away)}
                  >
                    <div className="team-name home">{match.home}</div>
                    <div className="vs-container">
                      <span className="vs">VS</span>
                      <span className="match-time">
                        {match.date} • {match.time}
                      </span>
                    </div>
                    <div className="team-name away">{match.away}</div>
                  </button>
                ))}
              </div>
            </>
          ) : (
            <div className="deep-dive-results">
              <h2 className="heading-secondary card-title">Model Deep Dive</h2>

              {predictionData.value_bets.length > 0 && (
                <div className="value-banner">
                  <h4 className="value-title">Value Bet Detected</h4>
                  {predictionData.value_bets.map((bet, index) => (
                    <div key={index} className="value-copy">
                      <strong>{bet.pick}</strong> shows positive expected value. Recommended stake:{' '}
                      <strong>{(bet.kelly * 100).toFixed(2)}%</strong> of bankroll.
                    </div>
                  ))}
                </div>
              )}

              <div className="info-panel">
                <h4 className="panel-title">Market Odds</h4>
                <div className="odds-row">
                  <div>
                    {homeTeam}: <strong>{predictionData.odds[0].toFixed(2)}</strong>
                  </div>
                  <div>
                    Draw: <strong>{predictionData.odds[1].toFixed(2)}</strong>
                  </div>
                  <div>
                    {awayTeam}: <strong>{predictionData.odds[2].toFixed(2)}</strong>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="panel-title">State Vectors</h4>
                <div className="feature-grid">
                  <div className="feature-card">
                    <strong>{homeTeam}</strong>
                    <div className="feature-line">
                      <span>Elo</span>
                      <span>{predictionData.home_features.elo.toFixed(0)}</span>
                    </div>
                    <div className="feature-line">
                      <span>SDI</span>
                      <span>{predictionData.home_features.sdi.toFixed(2)}</span>
                    </div>
                    <div className="feature-line">
                      <span>Form</span>
                      <span>{predictionData.home_features.form.toFixed(2)}</span>
                    </div>
                    <div className="feature-line">
                      <span>Sentiment</span>
                      <span>{predictionData.home_features.sent.toFixed(2)}</span>
                    </div>
                  </div>
                  <div className="feature-card">
                    <strong>{awayTeam}</strong>
                    <div className="feature-line">
                      <span>Elo</span>
                      <span>{predictionData.away_features.elo.toFixed(0)}</span>
                    </div>
                    <div className="feature-line">
                      <span>SDI</span>
                      <span>{predictionData.away_features.sdi.toFixed(2)}</span>
                    </div>
                    <div className="feature-line">
                      <span>Form</span>
                      <span>{predictionData.away_features.form.toFixed(2)}</span>
                    </div>
                    <div className="feature-line">
                      <span>Sentiment</span>
                      <span>{predictionData.away_features.sent.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {predictionData.historical_matches.length > 0 && (
                <div>
                  <h4 className="panel-title">Recent Head-to-Head</h4>
                  <div className="history-list">
                    {predictionData.historical_matches.map((match, index) => (
                      <div key={index} className="history-item">
                        <span className="history-date">{match.date}</span>
                        <span>
                          {match.home_team}{' '}
                          <strong>
                            {match.home_goals} - {match.away_goals}
                          </strong>{' '}
                          {match.away_team}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {predictionData.player_predictions && (
                <div className="mt-4">
                  <h4 className="panel-title flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                    Player Performance (Predicted)
                  </h4>
                  <div className="feature-grid">
                    <div className="feature-card border border-cyan-500/20 bg-gradient-to-br from-cyan-950/30 to-transparent">
                      <strong className="text-cyan-400 mb-2 block">{homeTeam} Key Players</strong>
                      {predictionData.player_predictions.home.map((player, idx) => (
                        <div key={idx} className="mb-3 last:mb-0 bg-black/40 p-2 rounded-md border border-white/5">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-semibold text-gray-200">{player.name}</span>
                            <span className="text-cyan-400 font-bold bg-cyan-900/40 px-1.5 py-0.5 rounded text-xs">
                              {player.predicted_rating.toFixed(1)}
                            </span>
                          </div>
                          <div className="grid grid-cols-4 gap-1 text-[10px] text-center mt-2">
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Tkl</div>
                              <div className="text-gray-300 font-bold">{player.stats.tackles}</div>
                            </div>
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Sht</div>
                              <div className="text-gray-300 font-bold">{player.stats.shots}</div>
                            </div>
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Drb</div>
                              <div className="text-gray-300 font-bold">{player.stats.dribbles}</div>
                            </div>
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Pas</div>
                              <div className="text-gray-300 font-bold">{player.stats.passes}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="feature-card border border-purple-500/20 bg-gradient-to-br from-purple-950/30 to-transparent">
                      <strong className="text-purple-400 mb-2 block">{awayTeam} Key Players</strong>
                      {predictionData.player_predictions.away.map((player, idx) => (
                        <div key={idx} className="mb-3 last:mb-0 bg-black/40 p-2 rounded-md border border-white/5">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-semibold text-gray-200">{player.name}</span>
                            <span className="text-purple-400 font-bold bg-purple-900/40 px-1.5 py-0.5 rounded text-xs">
                              {player.predicted_rating.toFixed(1)}
                            </span>
                          </div>
                          <div className="grid grid-cols-4 gap-1 text-[10px] text-center mt-2">
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Tkl</div>
                              <div className="text-gray-300 font-bold">{player.stats.tackles}</div>
                            </div>
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Sht</div>
                              <div className="text-gray-300 font-bold">{player.stats.shots}</div>
                            </div>
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Drb</div>
                              <div className="text-gray-300 font-bold">{player.stats.dribbles}</div>
                            </div>
                            <div className="bg-white/5 p-1 rounded">
                              <div className="text-gray-500 uppercase">Pas</div>
                              <div className="text-gray-300 font-bold">{player.stats.passes}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
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
