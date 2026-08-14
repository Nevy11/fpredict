import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState } from 'react'
import {
  Users,
  CalendarDays,
  Loader2,
  AlertCircle,
  BrainCircuit,
  Trophy,
  ChevronRight,
} from 'lucide-react'
import {
  fetchTowerCFixtures,
  fetchTowerCPrediction,
  type TowerCFixture,
  type TowerCPrediction,
  type TowerCPlayer,
} from '../lib/api'

export const Route = createFileRoute('/players')({
  component: PlayersPage,
  ssr: false,
})

function formatDate(dateStr: string) {
  const d = new Date(dateStr + 'T12:00:00')
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
}

function PlayerRow({ player, accent }: { player: TowerCPlayer; accent: 'cyan' | 'purple' }) {
  const ratingClass = accent === 'cyan' ? 'text-cyan-400 bg-cyan-900/40' : 'text-purple-400 bg-purple-900/40'
  return (
    <div className="bg-black/40 p-3 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
      <div className="flex justify-between items-start gap-2 mb-2">
        <div className="min-w-0">
          <div className="font-semibold text-white truncate">{player.name}</div>
          <span className="text-[10px] uppercase tracking-wider text-gray-500 font-bold">{player.position}</span>
        </div>
        <span className={`shrink-0 font-bold px-2 py-0.5 rounded text-xs ${ratingClass}`}>
          {player.predicted_rating.toFixed(1)}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-1 text-[10px] text-center">
        <StatCell label="MIN" value={player.expected.minutes} />
        <StatCell label="xG" value={player.expected.xg.toFixed(2)} />
        <StatCell label="Prog" value={player.expected.progressive_passes} />
        <StatCell label="Press" value={player.expected.pressing_regains} />
      </div>
    </div>
  )
}

function StatCell({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-white/5 p-1.5 rounded">
      <div className="text-gray-500 uppercase">{label}</div>
      <div className="text-gray-200 font-bold">{value}</div>
    </div>
  )
}

function MatchProbBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-400">{label}</span>
        <span className="font-bold text-white">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  )
}

function PlayersPage() {
  const [fixtures, setFixtures] = useState<TowerCFixture[]>([])
  const [selected, setSelected] = useState<TowerCFixture | null>(null)
  const [prediction, setPrediction] = useState<TowerCPrediction | null>(null)
  const [loadingFixtures, setLoadingFixtures] = useState(true)
  const [loadingPrediction, setLoadingPrediction] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoadingFixtures(true)
    fetchTowerCFixtures()
      .then(({ fixtures: loaded }) => {
        if (cancelled) return
        setFixtures(loaded)
        if (loaded.length > 0) setSelected(loaded[0])
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Failed to load fixtures')
      })
      .finally(() => {
        if (!cancelled) setLoadingFixtures(false)
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (!selected) return
    let cancelled = false
    setLoadingPrediction(true)
    setError('')
    fetchTowerCPrediction(selected.home_team, selected.away_team)
      .then((result) => {
        if (!cancelled) setPrediction(result)
      })
      .catch((err) => {
        if (!cancelled) {
          setPrediction(null)
          setError(err instanceof Error ? err.message : 'Tower C prediction failed')
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingPrediction(false)
      })
    return () => { cancelled = true }
  }, [selected])

  return (
    <div className="container page-stack pb-20">
      <header className="page-header flex flex-col items-center text-center mt-8 mb-10">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-cyan-400 text-sm font-semibold tracking-widest uppercase mb-6 backdrop-blur-md">
          <BrainCircuit size={16} />
          <span>Tower C · Lineup Synergy Model</span>
        </div>
        <h1 className="heading-primary text-5xl md:text-6xl mb-4">Player Intelligence</h1>
        <p className="subtitle text-lg max-w-2xl text-gray-400 mx-auto">
          Expected match outcomes and per-player performance vectors from the 11v11 synergy model — minutes, xG, progressive passes, and pressing regains.
        </p>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Fixtures sidebar */}
        <div className="xl:col-span-3 glass-card p-5 flex flex-col max-h-[820px]">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
            <CalendarDays size={18} className="text-cyan-400" />
            <h2 className="text-lg font-bold text-white">Upcoming Games</h2>
          </div>

          {loadingFixtures ? (
            <div className="flex items-center justify-center flex-1 text-gray-400 gap-2">
              <Loader2 size={20} className="animate-spin" />
              <span className="text-sm">Loading fixtures…</span>
            </div>
          ) : fixtures.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No upcoming fixtures found.</p>
          ) : (
            <div className="overflow-y-auto custom-scrollbar flex flex-col gap-2 pr-1">
              {fixtures.map((fixture) => {
                const isActive = selected?.id === fixture.id
                return (
                  <button
                    key={fixture.id}
                    type="button"
                    onClick={() => setSelected(fixture)}
                    className={`text-left p-3 rounded-xl border transition-all ${
                      isActive
                        ? 'bg-cyan-500/10 border-cyan-500/40 shadow-lg shadow-cyan-500/5'
                        : 'bg-black/20 border-white/5 hover:border-white/15 hover:bg-white/5'
                    }`}
                  >
                    <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1.5">
                      {formatDate(fixture.match_date)} · {fixture.competition}
                    </div>
                    <div className="font-semibold text-white text-sm leading-snug">
                      {fixture.home_team}
                    </div>
                    <div className="text-xs text-gray-500 my-0.5">vs</div>
                    <div className="font-semibold text-gray-300 text-sm leading-snug">
                      {fixture.away_team}
                    </div>
                    {isActive && <ChevronRight size={14} className="text-cyan-400 mt-2 ml-auto" />}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* Main prediction panel */}
        <div className="xl:col-span-9 flex flex-col gap-6">
          {error && (
            <div className="flex items-center gap-2 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
              <AlertCircle size={18} />
              {error}
            </div>
          )}

          {!selected ? (
            <div className="glass-card p-12 text-center text-gray-500">
              Select a fixture to run Tower C predictions.
            </div>
          ) : loadingPrediction ? (
            <div className="glass-card p-16 flex flex-col items-center justify-center text-gray-400 gap-3">
              <Loader2 size={32} className="animate-spin text-cyan-400" />
              <span>Running Tower C on {selected.home_team} vs {selected.away_team}…</span>
            </div>
          ) : prediction ? (
            <>
              {/* Match header + outcome */}
              <div className="glass-card p-6">
                <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-1">
                      {prediction.home_team}{' '}
                      <span className="text-gray-500 font-normal">vs</span>{' '}
                      {prediction.away_team}
                    </h2>
                    <p className="text-sm text-gray-500">
                      {selected ? formatDate(selected.match_date) : ''}
                      {' · '}
                      Source:{' '}
                      <span className={prediction.model_ready ? 'text-emerald-400' : 'text-amber-400'}>
                        {prediction.source === 'tower_c_model' ? 'Trained model' : 'Impact heuristic'}
                      </span>
                      {!prediction.lineup_complete && (
                        <span className="text-amber-400/80"> · Partial lineup (&lt;11 players)</span>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-gray-400">
                    <Trophy size={14} className="text-yellow-400" />
                    Match outcome (Tower C)
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MatchProbBar label={`${prediction.home_team} win`} value={prediction.match_probs.home} color="bg-cyan-500" />
                  <MatchProbBar label="Draw" value={prediction.match_probs.draw} color="bg-gray-400" />
                  <MatchProbBar label={`${prediction.away_team} win`} value={prediction.match_probs.away} color="bg-purple-500" />
                </div>
              </div>

              {/* Full lineups */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card p-5 border-cyan-500/20">
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
                    <Users size={18} className="text-cyan-400" />
                    <h3 className="font-bold text-cyan-400">{prediction.home_team}</h3>
                    <span className="ml-auto text-xs text-gray-500">{prediction.home_lineup.length} players</span>
                  </div>
                  <div className="flex flex-col gap-2 max-h-[520px] overflow-y-auto custom-scrollbar pr-1">
                    {prediction.home_lineup.map((player, idx) => (
                      <PlayerRow key={`${player.name}-${idx}`} player={player} accent="cyan" />
                    ))}
                  </div>
                </div>

                <div className="glass-card p-5 border-purple-500/20">
                  <div className="flex items-center gap-2 mb-4 pb-3 border-b border-white/10">
                    <Users size={18} className="text-purple-400" />
                    <h3 className="font-bold text-purple-400">{prediction.away_team}</h3>
                    <span className="ml-auto text-xs text-gray-500">{prediction.away_lineup.length} players</span>
                  </div>
                  <div className="flex flex-col gap-2 max-h-[520px] overflow-y-auto custom-scrollbar pr-1">
                    {prediction.away_lineup.map((player, idx) => (
                      <PlayerRow key={`${player.name}-${idx}`} player={player} accent="purple" />
                    ))}
                  </div>
                </div>
              </div>

              <p className="text-xs text-gray-600 text-center">
                Expected outcomes: minutes played, xG contribution, progressive passes, pressing regains, and predicted match rating (1–10 scale).
              </p>
            </>
          ) : null}
        </div>
      </div>
    </div>
  )
}
