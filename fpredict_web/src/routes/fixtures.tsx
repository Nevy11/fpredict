import { createFileRoute, Link } from '@tanstack/react-router'
import { CalendarDays, ChevronRight, ChevronLeft } from 'lucide-react'
import { useState } from 'react'

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

// Robust date parser for "MMM DD, YYYY"
const parseDateRobust = (dateStr: string) => {
  const months: Record<string, number> = {
    'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
    'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
  }
  const parts = dateStr.replace(',', '').split(' ')
  if (parts.length === 3) {
    const month = months[parts[0]] ?? 0
    const day = parseInt(parts[1], 10)
    const year = parseInt(parts[2], 10)
    return new Date(year, month, day)
  }
  return new Date(dateStr)
}

function Fixtures() {
  // Group fixtures by month and year
  const fixturesByMonth = MOCK_FIXTURES.reduce((acc, fixture) => {
    const dateObj = parseDateRobust(fixture.date)
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    const monthYear = `${monthNames[dateObj.getMonth()]} ${dateObj.getFullYear()}`
    
    if (!acc[monthYear]) {
      acc[monthYear] = []
    }
    acc[monthYear].push(fixture)
    return acc
  }, {} as Record<string, typeof MOCK_FIXTURES>)

  const monthYears = Object.keys(fixturesByMonth).sort((a, b) => {
    // "August 2026" -> parse roughly for sorting
    const dateA = new Date(a)
    const dateB = new Date(b)
    return (isNaN(dateA.getTime()) ? 0 : dateA.getTime()) - (isNaN(dateB.getTime()) ? 0 : dateB.getTime())
  })
  
  const [currentMonthIndex, setCurrentMonthIndex] = useState(0)
  const currentMonthYear = monthYears[currentMonthIndex]
  const currentFixtures = currentMonthYear ? fixturesByMonth[currentMonthYear] : []

  // Calendar calculations
  let daysInMonth = 30
  let firstDay = 0
  
  if (currentFixtures.length > 0) {
    const firstFixtureDate = parseDateRobust(currentFixtures[0].date)
    const year = firstFixtureDate.getFullYear()
    const month = firstFixtureDate.getMonth()
    daysInMonth = new Date(year, month + 1, 0).getDate()
    firstDay = new Date(year, month, 1).getDay()
  }

  const days = []
  for (let i = 0; i < firstDay; i++) {
    days.push(null)
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i)
  }

  const daysOfWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

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

      {monthYears.length > 0 && (
        <div className="max-w-6xl mx-auto w-full flex flex-col gap-6">
          {/* Calendar Controls */}
          <div className="flex items-center justify-between glass-card p-4 md:px-8 border border-white/10">
            <button 
              onClick={() => setCurrentMonthIndex(prev => Math.max(0, prev - 1))}
              disabled={currentMonthIndex === 0}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 transition-colors border border-white/10 hover:border-cyan-500/50 text-white"
            >
              <ChevronLeft size={24} />
            </button>
            
            <h2 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              {currentMonthYear}
            </h2>
            
            <button 
              onClick={() => setCurrentMonthIndex(prev => Math.min(monthYears.length - 1, prev + 1))}
              disabled={currentMonthIndex === monthYears.length - 1}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:hover:bg-white/5 transition-colors border border-white/10 hover:border-cyan-500/50 text-white"
            >
              <ChevronRight size={24} />
            </button>
          </div>

          {/* Calendar Grid */}
          <div className="glass-card p-4 md:p-8 border border-white/10 hover:border-cyan-500/30 transition-all duration-500">
            <div className="grid grid-cols-7 gap-2 md:gap-4 mb-4">
              {daysOfWeek.map(day => (
                <div key={day} className="text-center text-xs md:text-sm font-semibold text-gray-400 uppercase tracking-wider py-2">
                  {day}
                </div>
              ))}
            </div>
            
            <div className="grid grid-cols-7 gap-2 md:gap-4">
              {days.map((day, idx) => {
                if (day === null) {
                  return <div key={`empty-${idx}`} className="h-28 md:h-36 bg-black/20 rounded-xl border border-white/5 opacity-40" />
                }
                
                const dayFixtures = currentFixtures.filter(f => parseDateRobust(f.date).getDate() === day)
                const hasFixtures = dayFixtures.length > 0
                
                return (
                  <div 
                    key={`day-${day}`} 
                    className={`h-28 md:h-36 rounded-xl border p-1 md:p-3 flex flex-col gap-1 md:gap-2 overflow-y-auto custom-scrollbar transition-all duration-300
                      ${hasFixtures 
                        ? 'bg-black/60 border-white/10 hover:border-cyan-500/50 hover:bg-black/80 hover:shadow-[0_0_15px_rgba(0,240,255,0.05)]' 
                        : 'bg-black/20 border-white/5 opacity-60'
                      }`}
                  >
                    <span className={`text-xs md:text-sm font-bold ${hasFixtures ? 'text-cyan-400' : 'text-gray-500'}`}>
                      {day}
                    </span>
                    
                    <div className="flex flex-col gap-1.5">
                      {dayFixtures.map(match => (
                        <Link
                          key={`${match.home}-${match.away}`}
                          to="/"
                          search={{ home: match.home, away: match.away }}
                          className="group relative flex flex-col gap-1 p-2 rounded-lg bg-white/5 hover:bg-cyan-900/40 border border-white/5 hover:border-cyan-500/40 transition-all cursor-pointer"
                          title={`${match.home} vs ${match.away} @ ${match.time}`}
                        >
                          <div className="flex items-center justify-between gap-1 w-full">
                             <div className="flex items-center gap-1.5 truncate">
                               <div className={`shrink-0 w-1.5 h-1.5 rounded-full bg-gradient-to-br ${getTeamGradient(match.home)}`} />
                               <span className="text-[10px] md:text-xs text-gray-300 group-hover:text-white truncate font-medium">{getTeamInitial(match.home)}</span>
                             </div>
                             <span className="text-[8px] text-gray-500 font-bold shrink-0">VS</span>
                             <div className="flex items-center gap-1.5 truncate flex-row-reverse">
                               <div className={`shrink-0 w-1.5 h-1.5 rounded-full bg-gradient-to-br ${getTeamGradient(match.away)}`} />
                               <span className="text-[10px] md:text-xs text-gray-300 group-hover:text-white truncate font-medium">{getTeamInitial(match.away)}</span>
                             </div>
                          </div>
                          <div className="text-[10px] text-cyan-400 font-medium opacity-0 group-hover:opacity-100 transition-opacity absolute inset-0 bg-black/80 flex items-center justify-center rounded-lg backdrop-blur-sm shadow-[0_0_10px_rgba(0,240,255,0.2)]">
                            {match.time}
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

