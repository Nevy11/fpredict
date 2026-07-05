import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  fetchManagerLookup,
  fetchManagerNames,
  fetchManagerPrediction,
  fetchManagerProfile,
  fetchTeams,
  type ManagerLookupResult,
  type ManagerPredictionResult,
  type ManagerSide,
  type TacticalStyle,
} from '../lib/api'

const FALLBACK_TEAMS = [
  'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton & Hove Albion',
  'Chelsea', 'Coventry City', 'Crystal Palace', 'Everton', 'Fulham',
  'Hull City', 'Ipswich Town', 'Leeds United', 'Liverpool', 'Manchester City',
  'Manchester United', 'Newcastle United', 'Nottingham Forest', 'Sunderland', 'Tottenham Hotspur',
]

const STYLE_LABELS: Record<TacticalStyle, string> = {
  possession: 'Possession',
  pressing: 'High Press',
  counter: 'Counter',
  pragmatic: 'Pragmatic',
  balanced: 'Balanced',
}

const EMPTY_SIDE: ManagerSide = {
  name: '',
  team: '',
  nationality: '',
  tactical_style: 'balanced',
  formation: '4-3-3',
  inferred: false,
  history: [],
  form: { ppg: 0, win_rate: 0, matches: 0 },
}

function styleClass(style: string) {
  return `style-badge style-${style}`
}

function formatDelta(value: number) {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}

function ManagerCard({
  manager,
  side,
  teamLabel,
  managerOptions,
  selectedManager,
  onManagerChange,
  loading,
}: {
  manager: ManagerSide
  side: 'home' | 'away'
  teamLabel: string
  managerOptions: string[]
  selectedManager: string
  onManagerChange: (name: string) => void
  loading: boolean
}) {
  if (loading || !selectedManager) {
    return (
      <div className={`manager-card manager-card-${side} manager-card-loading`}>
        <div className="manager-card-shimmer" />
        <p>Resolving manager...</p>
      </div>
    )
  }

  return (
    <div className={`manager-card manager-card-${side}`}>
      <div className="manager-card-header">
        <span className="manager-side-label">{side === 'home' ? 'Home' : 'Away'}</span>
        <span className="manager-team-label">{teamLabel}</span>
      </div>

      <div className="input-group manager-override-group">
        <label className="input-label">Manager (override for what-if)</label>
        <select
          className="glass-input compact-input"
          value={selectedManager}
          onChange={(event) => onManagerChange(event.target.value)}
        >
          {managerOptions.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>

      <h3 className="manager-name">{manager.name}</h3>
      {manager.inferred && <span className="inferred-badge">Inferred from seed data</span>}

      <div className="manager-meta-grid">
        <div className="manager-meta-item">
          <span className="manager-meta-label">Tactical Style</span>
          <span className={styleClass(manager.tactical_style)}>{STYLE_LABELS[manager.tactical_style] ?? manager.tactical_style}</span>
        </div>
        <div className="manager-meta-item">
          <span className="manager-meta-label">Formation</span>
          <span className="manager-meta-value">{manager.formation}</span>
        </div>
        <div className="manager-meta-item">
          <span className="manager-meta-label">Nationality</span>
          <span className="manager-meta-value">{manager.nationality}</span>
        </div>
        <div className="manager-meta-item">
          <span className="manager-meta-label">Recent Form</span>
          <span className="manager-meta-value accent">{manager.form.ppg.toFixed(2)} PPG</span>
        </div>
        <div className="manager-meta-item">
          <span className="manager-meta-label">Win Rate</span>
          <span className="manager-meta-value">{(manager.form.win_rate * 100).toFixed(0)}%</span>
        </div>
        <div className="manager-meta-item">
          <span className="manager-meta-label">Sample</span>
          <span className="manager-meta-value">{manager.form.matches} matches</span>
        </div>
      </div>

      {manager.history.length > 0 && (
        <div className="manager-history">
          <h4 className="panel-title">Tenure History</h4>
          <ul className="tenure-list">
            {manager.history.map((tenure) => (
              <li key={`${tenure.team}-${tenure.start_date}`} className="tenure-item">
                <span className="tenure-team">{tenure.team}</span>
                <span className="tenure-dates">
                  {tenure.start_date.slice(0, 4)}
                  {' – '}
                  {tenure.is_current ? 'Present' : tenure.end_date?.slice(0, 4) ?? '—'}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function ProbabilityCompare({
  label,
  probs,
  accent,
}: {
  label: string
  probs: { home: number; draw: number; away: number }
  accent?: 'base' | 'manager' | 'blended'
}) {
  return (
    <div className={`prob-compare-block prob-compare-${accent ?? 'base'}`}>
      <h4 className="prob-compare-title">{label}</h4>
      <div className="prob-row">
        <div className="prob-header">
          <span className="prob-label">Home</span>
          <span className="prob-value">{probs.home.toFixed(2)}%</span>
        </div>
        <div className="prob-bar">
          <div className="prob-fill" style={{ width: `${probs.home}%` }} />
        </div>
      </div>
      <div className="prob-row">
        <div className="prob-header">
          <span className="prob-label">Draw</span>
          <span className="prob-value">{probs.draw.toFixed(2)}%</span>
        </div>
        <div className="prob-bar">
          <div className="prob-fill draw" style={{ width: `${probs.draw}%` }} />
        </div>
      </div>
      <div className="prob-row">
        <div className="prob-header">
          <span className="prob-label">Away</span>
          <span className="prob-value">{probs.away.toFixed(2)}%</span>
        </div>
        <div className="prob-bar">
          <div className="prob-fill away" style={{ width: `${probs.away}%` }} />
        </div>
      </div>
    </div>
  )
}

export function ManagersPage() {
  const [teams, setTeams] = useState<string[]>(FALLBACK_TEAMS)
  const [managerOptions, setManagerOptions] = useState<string[]>([])
  const [homeTeam, setHomeTeam] = useState('Manchester City')
  const [awayTeam, setAwayTeam] = useState('Arsenal')
  const [lookup, setLookup] = useState<ManagerLookupResult | null>(null)
  const [homeManager, setHomeManager] = useState('')
  const [awayManager, setAwayManager] = useState('')
  const [homeSide, setHomeSide] = useState<ManagerSide | null>(null)
  const [awaySide, setAwaySide] = useState<ManagerSide | null>(null)
  const [prediction, setPrediction] = useState<ManagerPredictionResult | null>(null)
  const [lookupLoading, setLookupLoading] = useState(false)
  const [predictLoading, setPredictLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchTeams()
      .then((loaded) => {
        if (loaded.length > 0) setTeams(loaded)
      })
      .catch(() => undefined)

    fetchManagerNames()
      .then(setManagerOptions)
      .catch(() => undefined)
  }, [])

  const runLookup = useCallback(async () => {
    if (homeTeam === awayTeam) return

    setLookupLoading(true)
    setError('')
    setPrediction(null)

    try {
      const result = await fetchManagerLookup(homeTeam, awayTeam)
      setLookup(result)
      setHomeManager(result.home.name)
      setAwayManager(result.away.name)
      setHomeSide(result.home)
      setAwaySide(result.away)
    } catch (err) {
      setLookup(null)
      setHomeSide(null)
      setAwaySide(null)
      setError(err instanceof Error ? err.message : 'Unable to resolve managers.')
    } finally {
      setLookupLoading(false)
    }
  }, [homeTeam, awayTeam])

  useEffect(() => {
    runLookup()
  }, [runLookup])

  const refreshManagerSide = async (side: 'home' | 'away', managerName: string) => {
    const team = side === 'home' ? homeTeam : awayTeam
    try {
      const profile = await fetchManagerProfile(managerName, team)
      if (side === 'home') setHomeSide(profile)
      else setAwaySide(profile)
    } catch {
      const fallback: ManagerSide = {
        name: managerName,
        team,
        nationality: 'Unknown',
        tactical_style: 'balanced',
        formation: '4-3-3',
        inferred: true,
        history: [],
        form: { ppg: 1.3, win_rate: 0.33, matches: 0 },
      }
      if (side === 'home') setHomeSide(fallback)
      else setAwaySide(fallback)
    }
  }

  const handleHomeManagerChange = (name: string) => {
    setHomeManager(name)
    setPrediction(null)
    void refreshManagerSide('home', name)
  }

  const handleAwayManagerChange = (name: string) => {
    setAwayManager(name)
    setPrediction(null)
    void refreshManagerSide('away', name)
  }

  const handlePredict = async () => {
    if (homeTeam === awayTeam) {
      setError('Home and away teams must be different.')
      return
    }

    setPredictLoading(true)
    setError('')

    try {
      const result = await fetchManagerPrediction({
        homeTeam,
        awayTeam,
        homeManager,
        awayManager,
      })
      setPrediction(result)
    } catch (err) {
      setPrediction(null)
      setError(err instanceof Error ? err.message : 'Manager prediction failed.')
    } finally {
      setPredictLoading(false)
    }
  }

  const deltas = useMemo(() => {
    if (!prediction) return null
    return {
      home: prediction.home - prediction.base_probs.home,
      draw: prediction.draw - prediction.base_probs.draw,
      away: prediction.away - prediction.base_probs.away,
    }
  }, [prediction])

  const optionList = useMemo(() => {
    const merged = new Set(managerOptions)
    if (homeManager) merged.add(homeManager)
    if (awayManager) merged.add(awayManager)
    return Array.from(merged).sort()
  }, [managerOptions, homeManager, awayManager])

  return (
    <div className="container page-stack managers-page">
      <header className="page-header">
        <h1 className="heading-primary">Manager Factor</h1>
        <p className="subtitle">
          Quantify tactical edge with manager form, style clash, and a 32% weighted sub-tower blend on top of the base ensemble.
        </p>
      </header>

      <div className="glass-card card-stack fixture-panel">
        <h2 className="heading-secondary card-title">Fixture Selection</h2>
        <p className="card-caption">Managers resolve automatically when you change teams. Override before predicting to simulate mid-season changes.</p>

        <div className="fixture-selectors">
          <div className="input-group">
            <label className="input-label">Home Team</label>
            <select className="glass-input" value={homeTeam} onChange={(e) => setHomeTeam(e.target.value)}>
              {teams.map((team) => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
          <div className="fixture-vs">VS</div>
          <div className="input-group">
            <label className="input-label">Away Team</label>
            <select className="glass-input" value={awayTeam} onChange={(e) => setAwayTeam(e.target.value)}>
              {teams.map((team) => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
        </div>

        {lookup?.fallback_mode && (
          <div className="status-banner fallback-banner">
            Running in seed-data fallback mode — database manager tables unavailable.
          </div>
        )}

        {error && <div className="status-banner error">{error}</div>}
      </div>

      <div className="manager-duel-grid">
        <ManagerCard
          manager={homeSide ?? { ...EMPTY_SIDE, team: homeTeam }}
          side="home"
          teamLabel={homeTeam}
          managerOptions={optionList}
          selectedManager={homeManager}
          onManagerChange={handleHomeManagerChange}
          loading={lookupLoading}
        />

        <div className="h2h-center-panel">
          <div className="h2h-icon">⚔</div>
          <h3 className="h2h-title">Manager H2H</h3>
          {lookup?.head_to_head ? (
            <>
              <div className="h2h-stat">
                <span className="h2h-number">{lookup.head_to_head.meetings}</span>
                <span className="h2h-label">Meetings</span>
              </div>
              <div className="h2h-breakdown">
                <div><strong>{lookup.head_to_head.home_manager_wins}</strong> home mgr wins</div>
                <div><strong>{lookup.head_to_head.draws}</strong> draws</div>
                <div><strong>{lookup.head_to_head.away_manager_wins}</strong> away mgr wins</div>
              </div>
            </>
          ) : (
            <p className="h2h-empty">{lookupLoading ? 'Loading...' : 'Select a fixture'}</p>
          )}

          <button
            type="button"
            className="btn-primary manager-predict-btn"
            disabled={predictLoading || lookupLoading || !homeManager || !awayManager}
            onClick={() => void handlePredict()}
          >
            {predictLoading ? 'Blending Models...' : 'Calculate Blended Probability'}
          </button>
        </div>

        <ManagerCard
          manager={awaySide ?? { ...EMPTY_SIDE, team: awayTeam }}
          side="away"
          teamLabel={awayTeam}
          managerOptions={optionList}
          selectedManager={awayManager}
          onManagerChange={handleAwayManagerChange}
          loading={lookupLoading}
        />
      </div>

      {prediction && deltas && (
        <div className="glass-card card-stack blend-results">
          <div className="blend-header">
            <h2 className="heading-secondary card-title">Probability Breakdown</h2>
            <div className="weight-pills">
              <span className="weight-pill base">Base Ensemble 68%</span>
              <span className="weight-pill manager">Manager Tower 32%</span>
            </div>
          </div>

          <div className="prob-compare-grid">
            <ProbabilityCompare label="Base Ensemble" probs={prediction.base_probs} accent="base" />
            <ProbabilityCompare label="Manager Tower" probs={prediction.manager_probs} accent="manager" />
            <ProbabilityCompare label="Blended Output" probs={prediction} accent="blended" />
          </div>

          <div className="shift-panel">
            <h4 className="panel-title">Manager Factor Shift (Blended − Base)</h4>
            <div className="shift-grid">
              <div className={`shift-item ${deltas.home >= 0 ? 'positive' : 'negative'}`}>
                <span>Home</span>
                <strong>{formatDelta(deltas.home)}</strong>
              </div>
              <div className={`shift-item ${deltas.draw >= 0 ? 'positive' : 'negative'}`}>
                <span>Draw</span>
                <strong>{formatDelta(deltas.draw)}</strong>
              </div>
              <div className={`shift-item ${deltas.away >= 0 ? 'positive' : 'negative'}`}>
                <span>Away</span>
                <strong>{formatDelta(deltas.away)}</strong>
              </div>
            </div>
          </div>

          {prediction.value_bets.length > 0 && (
            <div className="value-banner">
              <h4 className="value-title">Value Bet Signal</h4>
              {prediction.value_bets.map((bet, index) => (
                <div key={index} className="value-copy">
                  <strong>{bet.pick}</strong> — Kelly stake{' '}
                  <strong>{(bet.kelly * 100).toFixed(2)}%</strong> of bankroll after manager adjustment.
                </div>
              ))}
            </div>
          )}

          <div className="info-panel">
            <h4 className="panel-title">Market Odds</h4>
            <div className="odds-row">
              <div>{homeTeam}: <strong>{prediction.odds[0].toFixed(2)}</strong></div>
              <div>Draw: <strong>{prediction.odds[1].toFixed(2)}</strong></div>
              <div>{awayTeam}: <strong>{prediction.odds[2].toFixed(2)}</strong></div>
            </div>
          </div>
        </div>
      )}

      {!prediction && !lookupLoading && lookup && (
        <div className="empty-state managers-empty">
          <div className="empty-icon">◎</div>
          <h3>Ready to blend</h3>
          <p>Review the manager profiles above, override if needed, then calculate blended probabilities.</p>
        </div>
      )}
    </div>
  )
}
