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

export type TacticalStyle = 'possession' | 'pressing' | 'counter' | 'pragmatic' | 'balanced'

export type ManagerForm = {
  ppg: number
  win_rate: number
  matches: number
}

export type ManagerTenure = {
  team: string
  start_date: string
  end_date: string | null
  is_current: boolean
}

export type ManagerSide = {
  name: string
  team: string
  nationality: string
  tactical_style: TacticalStyle
  formation: string
  inferred: boolean
  history: ManagerTenure[]
  form: ManagerForm
}

export type ManagerHeadToHead = {
  meetings: number
  home_manager_wins: number
  away_manager_wins: number
  draws: number
}

export type ManagerLookupResult = {
  home: ManagerSide
  away: ManagerSide
  head_to_head: ManagerHeadToHead
  fallback_mode?: boolean
}

export type ProbabilityBundle = {
  home: number
  draw: number
  away: number
}

export type ManagerFactor = {
  weight: number
  features: Record<string, number>
  head_to_head: ManagerHeadToHead
}

export type ManagerPredictionResult = {
  home: number
  draw: number
  away: number
  base_probs: ProbabilityBundle
  manager_probs: ProbabilityBundle
  manager_factor: ManagerFactor
  managers: {
    home: ManagerSide
    away: ManagerSide
  }
  odds: [number, number, number]
  value_bets: Array<{ pick: string; kelly: number }>
  home_features: TeamFeatures
  away_features: TeamFeatures
  historical_matches: PredictionResult['historical_matches']
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

export function fetchManagerNames() {
  return request<{ managers: string[] }>('/managers').then((payload) => payload.managers)
}

export function fetchManagerLookup(homeTeam: string, awayTeam: string) {
  const params = new URLSearchParams({ home_team: homeTeam, away_team: awayTeam })
  return request<ManagerLookupResult>(`/managers/lookup?${params.toString()}`)
}

export function fetchManagerProfile(managerName: string, team?: string) {
  const query = team ? `?team=${encodeURIComponent(team)}` : ''
  return request<ManagerSide>(
    `/managers/${encodeURIComponent(managerName)}/profile${query}`,
  )
}

export function fetchManagerPrediction(params: {
  homeTeam: string
  awayTeam: string
  homeManager?: string | null
  awayManager?: string | null
}) {
  return request<ManagerPredictionResult>('/predict/manager', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      home_team: params.homeTeam,
      away_team: params.awayTeam,
      home_manager: params.homeManager ?? null,
      away_manager: params.awayManager ?? null,
    }),
  })
}
