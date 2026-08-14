import { createFileRoute } from '@tanstack/react-router'
import { useEffect, useState, type ReactNode } from 'react'
import {
  Trophy,
  Users,
  ArrowLeftRight,
  Sparkles,
  Crown,
  Shield,
  Target,
  CalendarDays,
  BrainCircuit,
  ChevronRight,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import { fetchFantasyGuide, type FantasyGuide, type FantasyPlayer } from '../lib/api'

export const Route = createFileRoute('/fantasy')({
  ssr: false,
  component: FantasyPage,
})

type Tab = 'squad' | 'transfers' | 'chips'

const POSITION_COLORS: Record<string, string> = {
  GK: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
  DEF: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
  MID: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  FWD: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
}

const FDR_COLORS = ['', 'text-emerald-400', 'text-green-400', 'text-yellow-400', 'text-orange-400', 'text-red-400']

const CHIP_RATING_STYLE: Record<string, string> = {
  High: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
  Medium: 'border-yellow-500/40 bg-yellow-500/10 text-yellow-300',
  Low: 'border-gray-500/40 bg-gray-500/10 text-gray-400',
}

function FantasyPage() {
  const [guide, setGuide] = useState<FantasyGuide | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState<Tab>('squad')
  const [gameweek, setGameweek] = useState<number | undefined>(undefined)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    fetchFantasyGuide(gameweek)
      .then((data) => {
        if (!cancelled) setGuide(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setGuide(null)
          setError(err instanceof Error ? err.message : 'Failed to load fantasy guide.')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [gameweek])

  return (
    <div className="container page-stack pb-20">
      <header className="page-header flex flex-col items-center text-center mt-8 mb-10">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-emerald-400 text-sm font-semibold tracking-widest uppercase mb-6 backdrop-blur-md">
          <Trophy size={16} />
          <span>Fantasy Engine</span>
        </div>
        <h1 className="heading-primary text-5xl md:text-6xl mb-4">FPL Strategy Hub</h1>
        <p className="subtitle text-lg max-w-2xl text-gray-400 mx-auto">
          Optimal squad picks, weekly transfer targets, and chip timing — powered by fixture difficulty and player projections.
        </p>
      </header>

      {loading && (
        <div className="status-banner flex items-center justify-center gap-3">
          <Loader2 className="animate-spin" size={18} />
          Building your fantasy guide…
        </div>
      )}

      {error && (
        <div className="status-banner error flex items-center gap-2">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {guide && !loading && (
        <>
          {/* GW Header + Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={<CalendarDays size={22} className="text-emerald-400" />}
              label="Gameweek"
              value={`GW${guide.gameweek}`}
              sub={guide.deadline}
              accent="emerald"
            />
            <StatCard
              icon={<Target size={22} className="text-cyan-400" />}
              label="XI Projected"
              value={`${guide.best_squad.starting_xi_projected.toFixed(0)} pts`}
              sub={`Captain: ${guide.best_squad.captain.name}`}
              accent="cyan"
            />
            <StatCard
              icon={<Users size={22} className="text-purple-400" />}
              label="Squad Value"
              value={`£${guide.budget.spent.toFixed(1)}m`}
              sub={`£${guide.budget.remaining.toFixed(1)}m ITB`}
              accent="purple"
            />
            <StatCard
              icon={<ArrowLeftRight size={22} className="text-amber-400" />}
              label="Transfer Call"
              value={guide.transfers.recommended_action}
              sub={guide.transfers.summary.slice(0, 60) + (guide.transfers.summary.length > 60 ? '…' : '')}
              accent="amber"
            />
          </div>

          {/* Weekly Guidance */}
          <div className="glass-card p-6 mb-8 border-emerald-500/20">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500/20 flex items-center justify-center text-emerald-400">
                <BrainCircuit size={20} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white">This Week&apos;s Guide</h2>
                <p className="text-xs text-emerald-400/80 uppercase tracking-wider font-semibold">GW{guide.gameweek} Action Plan</p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                <label className="text-xs text-gray-400 uppercase tracking-wider">View GW</label>
                <select
                  className="glass-input text-sm py-1 px-2"
                  value={gameweek ?? guide.gameweek}
                  onChange={(e) => setGameweek(Number(e.target.value))}
                >
                  {Array.from({ length: 38 }, (_, i) => i + 1).map((gw) => (
                    <option key={gw} value={gw}>GW{gw}</option>
                  ))}
                </select>
              </div>
            </div>
            <ul className="space-y-2">
              {guide.guidance.map((tip, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300 leading-relaxed">
                  <ChevronRight size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                  {tip}
                </li>
              ))}
            </ul>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mb-6 flex-wrap">
            {([
              ['squad', 'Best Squad', Users],
              ['transfers', 'Transfers', ArrowLeftRight],
              ['chips', 'Free Chips', Sparkles],
            ] as const).map(([id, label, Icon]) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                  tab === id
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                    : 'bg-white/5 text-gray-400 border border-white/10 hover:bg-white/10'
                }`}
              >
                <Icon size={16} />
                {label}
              </button>
            ))}
          </div>

          {tab === 'squad' && <BestSquadTab guide={guide} />}
          {tab === 'transfers' && <TransfersTab guide={guide} />}
          {tab === 'chips' && <ChipsTab guide={guide} />}
        </>
      )}
    </div>
  )
}

const STAT_ACCENTS = {
  emerald: 'border-l-emerald-500',
  cyan: 'border-l-cyan-500',
  purple: 'border-l-purple-500',
  amber: 'border-l-amber-500',
} as const

function StatCard({
  icon, label, value, sub, accent,
}: {
  icon: ReactNode
  label: string
  value: string
  sub: string
  accent: keyof typeof STAT_ACCENTS
}) {
  return (
    <div className={`glass-card p-5 border-l-4 ${STAT_ACCENTS[accent]}`}>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
          {icon}
        </div>
        <div className="min-w-0">
          <div className="text-xs text-gray-400 uppercase tracking-wider font-semibold">{label}</div>
          <div className="text-2xl font-black text-white truncate">{value}</div>
          <div className="text-xs text-gray-500 truncate">{sub}</div>
        </div>
      </div>
    </div>
  )
}

function BestSquadTab({ guide }: { guide: FantasyGuide }) {
  const { best_squad: squad } = guide
  const startingIds = new Set(squad.starting_xi.map((p) => p.id))

  const byLine: Record<string, FantasyPlayer[]> = { GK: [], DEF: [], MID: [], FWD: [] }
  for (const p of squad.starting_xi) {
    byLine[p.position]?.push(p)
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
      {/* Pitch View */}
      <div className="lg:col-span-2 glass-card p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Recommended Squad</h2>
          <span className="text-sm text-gray-400 font-medium">{squad.formation} · £{guide.budget.spent.toFixed(1)}m</span>
        </div>

        {/* Pitch */}
        <div className="relative rounded-2xl border border-emerald-500/20 bg-gradient-to-b from-emerald-950/40 to-emerald-900/20 p-6 min-h-[420px] flex flex-col justify-between gap-4">
          <div className="absolute inset-4 border border-white/10 rounded-xl pointer-events-none" />
          <div className="absolute top-1/2 left-4 right-4 h-px bg-white/10" />

          {(['FWD', 'MID', 'DEF', 'GK'] as const).map((line) => (
            <div key={line} className="flex justify-center gap-3 flex-wrap relative z-10">
              {byLine[line].map((player) => (
                <PitchPlayer
                  key={player.id}
                  player={player}
                  isCaptain={player.id === squad.captain.id}
                  isVice={player.id === squad.vice_captain.id}
                />
              ))}
            </div>
          ))}
        </div>

        {/* Bench */}
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Bench</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {squad.bench.map((player) => (
              <BenchPlayer key={player.id} player={player} />
            ))}
          </div>
        </div>
      </div>

      {/* Squad Table */}
      <div className="glass-card p-6 flex flex-col max-h-[700px]">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield size={18} className="text-emerald-400" />
          Full Squad
        </h2>
        <div className="overflow-y-auto custom-scrollbar flex-1">
          <table className="data-table w-full">
            <thead className="sticky top-0 bg-black/80 backdrop-blur-md z-10">
              <tr>
                <th>Player</th>
                <th>Fix</th>
                <th>Pts</th>
              </tr>
            </thead>
            <tbody>
              {squad.players.map((player) => (
                <tr key={player.id} className={startingIds.has(player.id) ? 'bg-emerald-500/5' : 'opacity-60'}>
                  <td>
                    <div className="font-semibold text-white text-sm flex items-center gap-1">
                      {player.id === squad.captain.id && <Crown size={12} className="text-yellow-400" />}
                      {player.name}
                    </div>
                    <div className="text-xs text-gray-400">{player.position} · {player.team}</div>
                  </td>
                  <td>
                    <div className="text-xs text-gray-300">{player.next_fixture}</div>
                    <div className={`text-xs font-bold ${FDR_COLORS[player.fixture_difficulty]}`}>
                      FDR {player.fixture_difficulty}
                    </div>
                  </td>
                  <td className="text-cyan-400 font-medium text-sm">{player.projected_points.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="mt-4 pt-4 border-t border-white/10 text-xs text-gray-500">
          Data: {guide.data_source} · Season projection basis
        </div>
      </div>
    </div>
  )
}

function PitchPlayer({
  player, isCaptain, isVice,
}: {
  player: FantasyPlayer
  isCaptain: boolean
  isVice: boolean
}) {
  return (
    <div className="flex flex-col items-center gap-1 w-24">
      <div className={`relative w-16 h-16 rounded-full border-2 flex items-center justify-center text-xs font-black ${POSITION_COLORS[player.position]}`}>
        {player.position}
        {isCaptain && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-yellow-400 text-black text-[10px] flex items-center justify-center font-black">C</span>
        )}
        {isVice && !isCaptain && (
          <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-gray-400 text-black text-[10px] flex items-center justify-center font-black">V</span>
        )}
      </div>
      <div className="text-[11px] font-semibold text-white text-center leading-tight">{player.name.split(' ').pop()}</div>
      <div className="text-[10px] text-gray-400">{player.next_fixture}</div>
    </div>
  )
}

function BenchPlayer({ player }: { player: FantasyPlayer }) {
  return (
    <div className="bg-black/30 border border-white/5 rounded-lg p-3">
      <div className="flex items-center justify-between mb-1">
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${POSITION_COLORS[player.position]}`}>{player.position}</span>
        <span className={`text-[10px] font-bold ${FDR_COLORS[player.fixture_difficulty]}`}>FDR {player.fixture_difficulty}</span>
      </div>
      <div className="text-sm font-semibold text-white truncate">{player.name}</div>
      <div className="text-xs text-gray-400">{player.next_fixture}</div>
    </div>
  )
}

function TransfersTab({ guide }: { guide: FantasyGuide }) {
  const { transfers } = guide

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <div className="glass-card p-6">
        <h2 className="text-2xl font-bold text-white mb-2">Recommended Transfers</h2>
        <p className="text-sm text-gray-400 mb-6">GW{transfers.gameweek} · {transfers.free_transfers} free transfer{transfers.free_transfers !== 1 ? 's' : ''}</p>

        {transfers.recommended_action === 'Hold' ? (
          <div className="bg-emerald-900/20 border border-emerald-500/20 rounded-xl p-6 text-center">
            <div className="text-4xl mb-3">✋</div>
            <h3 className="text-xl font-bold text-emerald-300 mb-2">Hold Your Transfers</h3>
            <p className="text-sm text-gray-300 leading-relaxed">{transfers.summary}</p>
          </div>
        ) : (
          <div className="space-y-4">
            {transfers.transfers.map((t, i) => (
              <div key={i} className="bg-black/30 border border-white/10 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className={`text-xs font-bold px-2 py-1 rounded ${
                    t.priority === 'High' ? 'bg-red-500/20 text-red-300' :
                    t.priority === 'Medium' ? 'bg-yellow-500/20 text-yellow-300' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>{t.priority} Priority</span>
                  <span className="text-emerald-400 font-bold text-sm">+{t.points_gain.toFixed(1)} pts</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="flex-1 text-right">
                    <div className="text-sm font-semibold text-red-300">{t.out.name}</div>
                    <div className="text-xs text-gray-500">{t.out.team} · £{t.out.price}m</div>
                  </div>
                  <ArrowLeftRight size={20} className="text-gray-500 shrink-0" />
                  <div className="flex-1">
                    <div className="text-sm font-semibold text-emerald-300">{t.in.name}</div>
                    <div className="text-xs text-gray-500">{t.in.team} · £{t.in.price}m</div>
                  </div>
                </div>
                <p className="text-xs text-gray-400 mt-3 leading-relaxed">{t.reason}</p>
                {t.cost_delta !== 0 && (
                  <p className="text-xs text-gray-500 mt-1">
                    Cost change: {t.cost_delta > 0 ? '+' : ''}£{t.cost_delta.toFixed(1)}m
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-4">Transfer Radar</h2>
        <p className="text-sm text-gray-400 mb-4">Top moves if you have multiple transfers or a hit is worth it.</p>
        {transfers.all_suggestions.length === 0 ? (
          <p className="text-gray-500 text-sm">Your squad is already optimised for this gameweek.</p>
        ) : transfers.recommended_action === 'Hold' ? (
          <div className="space-y-3">
            <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Players to Watch</p>
            {transfers.all_suggestions.map((t, i) => (
              <div key={i} className="flex items-center justify-between bg-black/20 rounded-lg p-3 border border-white/5">
                <div className="text-sm">
                  <span className="text-emerald-400 font-semibold">{t.in.name}</span>
                  <span className="text-gray-500 text-xs ml-2">{t.in.team} · {t.in.next_fixture}</span>
                </div>
                <span className="text-cyan-400 text-sm font-bold">{t.in.projected_points.toFixed(0)} pts</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {transfers.all_suggestions.map((t, i) => (
              <div key={i} className="flex items-center justify-between bg-black/20 rounded-lg p-3 border border-white/5">
                <div className="text-sm">
                  <span className="text-red-400">{t.out.name}</span>
                  <span className="text-gray-500 mx-2">→</span>
                  <span className="text-emerald-400">{t.in.name}</span>
                </div>
                <span className="text-cyan-400 text-sm font-bold">+{t.points_gain.toFixed(1)}</span>
              </div>
            ))}
          </div>
        )}

        <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
          <h3 className="text-sm font-bold text-white mb-2">Transfer Rules Reminder</h3>
          <ul className="text-xs text-gray-400 space-y-1">
            <li>· 1 free transfer per week (max 2 banked)</li>
            <li>· Each extra transfer costs −4 points</li>
            <li>· Max 3 players from the same team</li>
            <li>· Only activate Wildcard or Free Hit when the guide rates them High</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

function ChipsTab({ guide }: { guide: FantasyGuide }) {
  const { chips } = guide

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {chips.chips.map((chip) => (
          <div
            key={chip.chip}
            className={`glass-card p-6 border ${CHIP_RATING_STYLE[chip.rating]}`}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold text-white">{chip.chip}</h3>
                <p className="text-xs text-gray-400 mt-1">{chip.status}</p>
              </div>
              <span className={`text-xs font-bold px-3 py-1 rounded-full border ${CHIP_RATING_STYLE[chip.rating]}`}>
                {chip.rating}
              </span>
            </div>
            <div className="mb-3">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Best Window</div>
              <div className="text-sm font-semibold text-white">{chip.recommended_window}</div>
            </div>
            <p className="text-sm text-gray-300 leading-relaxed">{chip.advice}</p>
          </div>
        ))}
      </div>

      <div className="glass-card p-6">
        <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Sparkles size={18} className="text-purple-400" />
          Chip Priority Order
        </h2>
        <ol className="space-y-2">
          {chips.priority_order.map((item, i) => (
            <li key={i} className="flex items-center gap-3 text-sm text-gray-300">
              <span className="w-6 h-6 rounded-full bg-purple-500/20 text-purple-300 flex items-center justify-center text-xs font-bold">{i + 1}</span>
              {item}
            </li>
          ))}
        </ol>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6 pt-6 border-t border-white/10">
          <div>
            <h3 className="text-sm font-bold text-white mb-2">Blank Gameweeks</h3>
            <div className="flex flex-wrap gap-2">
              {chips.calendar_notes.blank_gameweeks.map((gw) => (
                <span key={gw} className="px-2 py-1 rounded bg-orange-500/20 text-orange-300 text-xs font-bold">GW{gw}</span>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">Fewer teams play — plan Free Hits or bench fodder carefully.</p>
          </div>
          <div>
            <h3 className="text-sm font-bold text-white mb-2">Double Gameweeks</h3>
            <div className="flex flex-wrap gap-2">
              {chips.calendar_notes.double_gameweeks.map((gw) => (
                <span key={gw} className="px-2 py-1 rounded bg-cyan-500/20 text-cyan-300 text-xs font-bold">GW{gw}</span>
              ))}
            </div>
            <p className="text-xs text-gray-500 mt-2">Two fixtures per team — ideal for Bench Boost and Triple Captain.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
