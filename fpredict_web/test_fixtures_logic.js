const MOCK_FIXTURES = [
  { matchweek: 1, home: 'Manchester City', away: 'Arsenal', date: 'Aug 21, 2026', time: '20:00 BST' }
];

const fixturesByMonth = MOCK_FIXTURES.reduce((acc, fixture) => {
    const dateObj = new Date(fixture.date)
    const monthYear = dateObj.toLocaleString('en-US', { month: 'long', year: 'numeric' })
    if (!acc[monthYear]) {
      acc[monthYear] = []
    }
    acc[monthYear].push(fixture)
    return acc
  }, {})

const monthYears = Object.keys(fixturesByMonth).sort((a, b) => new Date(a).getTime() - new Date(b).getTime())
console.log(monthYears);
