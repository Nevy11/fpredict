const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type PredictionResult = {
  home: number
  draw: number
  away: number
  odds: [number, number, number]
  value_bets: Array<{ pick: string; kelly: number }>
  home_features: TeamFeatures
  away_features: TeamFeatures
  historical_matches: Array<{
    date: string
    home_team: string
    away_team: string
    home_goals: number
    away_goals: number
  }>
}

export type TeamFeatures = {
  elo: number
  power: number
  sdi: number
  form: number
  sent: number
  gd: number
}

export type FeatureSnapshot = {
  date: string
  gameweek: string
  elo: number
  sdi: number
  form: number
  sentiment: number
  squad_power: number
}

export type FeatureSeries = {
  team: string
  snapshots: FeatureSnapshot[]
  summary: {
    avg_elo: number
    latest_elo: number
    latest_sdi: number
    latest_form: number
    sentiment_volatility: 'Low' | 'Medium' | 'High'
    market_overround: number
  }
}

export type BacktestResult = {
  season: string
  initial_bankroll: number
  final_bankroll: number
  roi: number
  total_bets: number
  wins: number
  win_rate: number
  equity_curve: Array<{ date: string; bankroll: number }>
  recent_bets: Array<{
    date: string
    match: string
    pick: string
    won: boolean
    bankroll: number
  }>
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const detail = await response.text()
    throw new Error(detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

export function fetchTeams() {
  return request<string[]>('/teams')
}

export function fetchPrediction(homeTeam: string, awayTeam: string) {
  return request<PredictionResult>('/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ home_team: homeTeam, away_team: awayTeam }),
  })
}

export function fetchFeatureSeries(team: string) {
  return request<FeatureSeries>(`/features/${encodeURIComponent(team)}`)
}

export function runBacktest(params: {
  season: string
  initial_bankroll: number
  kelly_fraction: number
}) {
  return request<BacktestResult>('/backtest', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
}
