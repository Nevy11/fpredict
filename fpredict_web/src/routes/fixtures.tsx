import { createFileRoute, Link } from '@tanstack/react-router'

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

function Fixtures() {
  const matchweeks = Array.from(new Set(MOCK_FIXTURES.map((f) => f.matchweek))).sort((a, b) => a - b)

  return (
    <div className="container page-stack">
      <header className="page-header">
        <h1 className="heading-primary">All Fixtures</h1>
        <p className="subtitle">Select a fixture to run the predictive engine.</p>
      </header>

      <div className="grid-1">
        {matchweeks.map((week) => (
          <div key={week} className="glass-card card-stack">
            <h2 className="heading-secondary card-title">Matchweek {week}</h2>
            <div className="schedule-list">
              {MOCK_FIXTURES.filter((f) => f.matchweek === week).map((match) => (
                <Link
                  to="/"
                  search={{ home: match.home, away: match.away }}
                  className="match-item match-button"
                  key={`${match.home}-${match.away}`}
                >
                  <div className="team-name home">{match.home}</div>
                  <div className="vs-container">
                    <span className="vs">VS</span>
                    <span className="match-time">
                      {match.date} &bull; {match.time}
                    </span>
                  </div>
                  <div className="team-name away">{match.away}</div>
                </Link>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
