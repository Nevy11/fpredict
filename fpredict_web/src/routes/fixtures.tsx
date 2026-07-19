import { createFileRoute, Link } from '@tanstack/react-router'
import { CalendarDays, ChevronRight } from 'lucide-react'

export const Route = createFileRoute('/fixtures')({
  component: Fixtures,
})

// Expanded mock fixtures for a few matchweeks
const MOCK_FIXTURES = [
  // Matchweek 1
  { matchweek: 1, home: 'Manchester City', away: 'Arsenal', date: 'Aug 21, 2026', time: '20:00 BST' },
  { matchweek: 1, home: 'Coventry City', away: 'Chelsea', date: 'Aug 22, 2026', time: '12:30 BST' },
  { matchweek: 1, home: 'Liverpool', away: 'Aston Villa', date: 'Aug 22, 2026', time: '15:00 BST' },
  { matchweek: 1, home: 'Sunderland', away: 'Newcastle United', date: 'Aug 22, 2026', time: '15:00 BST' },
  { matchweek: 1, home: 'Tottenham Hotspur', away: 'Everton', date: 'Aug 22, 2026', time: '17:30 BST' },
  { matchweek: 1, home: 'Manchester United', away: 'Leeds United', date: 'Aug 23, 2026', time: '14:00 BST' },
  { matchweek: 1, home: 'Hull City', away: 'Ipswich Town', date: 'Aug 23, 2026', time: '16:30 BST' },
  { matchweek: 1, home: 'Brighton & Hove Albion', away: 'Bournemouth', date: 'Aug 24, 2026', time: '20:00 BST' },
  { matchweek: 1, home: 'Brentford', away: 'Nottingham Forest', date: 'Aug 24, 2026', time: '20:00 BST' },
  { matchweek: 1, home: 'Crystal Palace', away: 'Fulham', date: 'Aug 24, 2026', time: '20:00 BST' },
  // Matchweek 2
  { matchweek: 2, home: 'Arsenal', away: 'Liverpool', date: 'Aug 28, 2026', time: '20:00 BST' },
  { matchweek: 2, home: 'Chelsea', away: 'Manchester United', date: 'Aug 29, 2026', time: '12:30 BST' },
  { matchweek: 2, home: 'Aston Villa', away: 'Tottenham Hotspur', date: 'Aug 29, 2026', time: '15:00 BST' },
  { matchweek: 2, home: 'Newcastle United', away: 'Manchester City', date: 'Aug 29, 2026', time: '15:00 BST' },
  { matchweek: 2, home: 'Everton', away: 'Sunderland', date: 'Aug 29, 2026', time: '17:30 BST' },
  { matchweek: 2, home: 'Leeds United', away: 'Hull City', date: 'Aug 30, 2026', time: '14:00 BST' },
  { matchweek: 2, home: 'Ipswich Town', away: 'Coventry City', date: 'Aug 30, 2026', time: '16:30 BST' },
  { matchweek: 2, home: 'Bournemouth', away: 'Brighton & Hove Albion', date: 'Aug 31, 2026', time: '20:00 BST' },
  { matchweek: 2, home: 'Nottingham Forest', away: 'Brentford', date: 'Aug 31, 2026', time: '20:00 BST' },
  { matchweek: 2, home: 'Fulham', away: 'Crystal Palace', date: 'Aug 31, 2026', time: '20:00 BST' },
  // Matchweek 3
  { matchweek: 3, home: 'Manchester City', away: 'Chelsea', date: 'Sep 11, 2026', time: '12:30 BST' },
  { matchweek: 3, home: 'Liverpool', away: 'Arsenal', date: 'Sep 11, 2026', time: '15:00 BST' },
  { matchweek: 3, home: 'Tottenham Hotspur', away: 'Aston Villa', date: 'Sep 11, 2026', time: '15:00 BST' },
  { matchweek: 3, home: 'Manchester United', away: 'Newcastle United', date: 'Sep 11, 2026', time: '17:30 BST' },
  { matchweek: 3, home: 'Coventry City', away: 'Ipswich Town', date: 'Sep 12, 2026', time: '14:00 BST' },
  { matchweek: 3, home: 'Sunderland', away: 'Everton', date: 'Sep 12, 2026', time: '16:30 BST' },
  { matchweek: 3, home: 'Hull City', away: 'Leeds United', date: 'Sep 12, 2026', time: '16:30 BST' },
  { matchweek: 3, home: 'Brighton & Hove Albion', away: 'Bournemouth', date: 'Sep 13, 2026', time: '20:00 BST' },
  { matchweek: 3, home: 'Brentford', away: 'Nottingham Forest', date: 'Sep 13, 2026', time: '20:00 BST' },
  { matchweek: 3, home: 'Crystal Palace', away: 'Fulham', date: 'Sep 13, 2026', time: '20:00 BST' },
]

// Helper to get a consistent gradient for a team based on its name
const getTeamGradient = (name: string) => {
  const gradients = [
    'from-cyan-500 to-blue-600',
    'from-purple-500 to-indigo-600',
    'from-rose-500 to-red-600',
    'from-emerald-400 to-teal-600',
    'from-amber-400 to-orange-500',
    'from-fuchsia-500 to-pink-600',
    'from-sky-400 to-blue-500',
  ]
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const index = Math.abs(hash) % gradients.length
  return gradients[index]
}

const getTeamInitial = (name: string) => {
  return name.substring(0, 3).toUpperCase()
}

function Fixtures() {
  const matchweeks = Array.from(new Set(MOCK_FIXTURES.map((f) => f.matchweek))).sort((a, b) => a - b)

  return (
    <div className="container page-stack relative pb-20">
      {/* Background glowing blob */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[300px] bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none -z-10" />

      <header className="page-header flex flex-col items-center text-center mt-8 mb-16">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-cyan-400 text-sm font-semibold tracking-widest uppercase mb-6 backdrop-blur-md shadow-[0_0_15px_rgba(0,240,255,0.1)]">
          <CalendarDays size={16} />
          <span>Season Schedule</span>
        </div>
        <h1 className="heading-primary text-5xl md:text-6xl mb-4">All Fixtures</h1>
        <p className="subtitle text-lg md:text-xl max-w-2xl text-gray-400 mx-auto">
          Select any fixture across the season to initialize the predictive engine and uncover algorithmic value bets.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-8 w-full">
        {matchweeks.map((week) => {
          const fixturesInWeek = MOCK_FIXTURES.filter((f) => f.matchweek === week)
          return (
            <div key={week} className="glass-card relative group overflow-hidden flex flex-col h-full border border-white/10 hover:border-cyan-500/30 transition-all duration-500 p-6 md:p-8 !h-[550px]">
              {/* Inner top gradient highlight */}
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-cyan-500 to-blue-600 opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
              
              <div className="flex items-center justify-between mb-6 pb-4 border-b border-white/5">
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
                  Matchweek {week}
                </h2>
                <span className="text-xs font-medium px-3 py-1 bg-white/5 border border-white/10 rounded-full text-gray-400">
                  {fixturesInWeek.length} Matches
                </span>
              </div>
              
              <div className="flex flex-col gap-3 flex-1 overflow-y-auto pr-2 schedule-list pb-2">
                {fixturesInWeek.map((match) => (
                  <Link
                    to="/"
                    search={{ home: match.home, away: match.away }}
                    className="relative flex items-center p-4 rounded-xl bg-black/30 border border-white/5 hover:bg-black/50 hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(0,240,255,0.1)] hover:-translate-y-1 transition-all duration-300 group/match"
                    key={`${match.home}-${match.away}`}
                  >
                    {/* Home Team */}
                    <div className="flex-1 flex flex-col items-end gap-1">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-sm text-gray-300 group-hover/match:text-white transition-colors text-right leading-tight">
                          {match.home}
                        </span>
                        <div className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-lg bg-gradient-to-br ${getTeamGradient(match.home)}`}>
                          {getTeamInitial(match.home)}
                        </div>
                      </div>
                    </div>

                    {/* VS Info */}
                    <div className="flex flex-col items-center justify-center px-4 min-w-[90px]">
                      <div className="text-xs font-black text-cyan-500/80 group-hover/match:text-cyan-400 tracking-widest mb-1 transition-colors">VS</div>
                      <div className="text-[10px] text-gray-500 font-medium whitespace-nowrap">{match.date}</div>
                      <div className="text-[10px] text-gray-500 font-medium whitespace-nowrap">{match.time}</div>
                    </div>

                    {/* Away Team */}
                    <div className="flex-1 flex flex-col items-start gap-1">
                      <div className="flex items-center gap-3 flex-row-reverse">
                        <span className="font-semibold text-sm text-gray-300 group-hover/match:text-white transition-colors text-left leading-tight">
                          {match.away}
                        </span>
                        <div className={`shrink-0 w-9 h-9 rounded-full flex items-center justify-center text-[10px] font-bold text-white shadow-lg bg-gradient-to-br ${getTeamGradient(match.away)}`}>
                          {getTeamInitial(match.away)}
                        </div>
                      </div>
                    </div>
                    
                    {/* Hover indicator arrow */}
                    <div className="absolute right-3 opacity-0 -translate-x-2 group-hover/match:opacity-100 group-hover/match:translate-x-0 transition-all duration-300 text-cyan-400">
                      <ChevronRight size={18} />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

