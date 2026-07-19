import { supabase } from './supabase'

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

export async function fetchManagerNames() {
  const { data, error } = await supabase.from('current_managers').select('manager_name')
  if (!error && data) {
    return Array.from(new Set(data.map(d => d.manager_name)))
  }
  return request<{ managers: string[] }>('/managers').then((payload) => payload.managers)
}

export async function fetchManagerLookup(homeTeam: string, awayTeam: string) {
  const { data, error } = await supabase.from('current_managers')
    .select('*')
    .in('team_name', [homeTeam, awayTeam])

  if (!error && data && data.length > 0) {
    const homeData = data.find(d => d.team_name === homeTeam)
    const awayData = data.find(d => d.team_name === awayTeam)

    const calcForm = (last_5: string[]) => {
      if (!last_5 || last_5.length === 0) return { ppg: 1.3, win_rate: 0.33, matches: 0 }
      let pts = 0; let wins = 0;
      for (const res of last_5) {
        if (res === 'W') { pts += 3; wins += 1 }
        else if (res === 'D') pts += 1
      }
      return { ppg: pts / last_5.length, win_rate: wins / last_5.length, matches: last_5.length }
    }

    const createSide = (d: any, team: string): ManagerSide => {
      if (!d) return {
        name: 'Unknown', team, nationality: 'Unknown', tactical_style: 'balanced',
        formation: '4-3-3', inferred: true, history: [], form: { ppg: 0, win_rate: 0, matches: 0 }
      }
      return {
        name: d.manager_name,
        team: d.team_name,
        nationality: 'Unknown',
        tactical_style: (d.tactical_style || 'balanced') as TacticalStyle,
        formation: '4-3-3',
        inferred: false,
        history: [],
        form: calcForm(d.last_5_games)
      }
    }

    // Try to get H2H from backend in the background or just return mock
    return {
      home: createSide(homeData, homeTeam),
      away: createSide(awayData, awayTeam),
      head_to_head: { meetings: 0, home_manager_wins: 0, away_manager_wins: 0, draws: 0 }
    }
  }

  const params = new URLSearchParams({ home_team: homeTeam, away_team: awayTeam })
  return request<ManagerLookupResult>(`/managers/lookup?${params.toString()}`)
}

export async function fetchManagerProfile(managerName: string, team?: string) {
  const { data, error } = await supabase.from('current_managers')
    .select('*')
    .eq('manager_name', managerName)
    .limit(1)

  if (!error && data && data.length > 0) {
    const d = data[0]
    const calcForm = (last_5: string[]) => {
      if (!last_5 || last_5.length === 0) return { ppg: 1.3, win_rate: 0.33, matches: 0 }
      let pts = 0; let wins = 0;
      for (const res of last_5) {
        if (res === 'W') { pts += 3; wins += 1 }
        else if (res === 'D') pts += 1
      }
      return { ppg: pts / last_5.length, win_rate: wins / last_5.length, matches: last_5.length }
    }
    return {
      name: d.manager_name,
      team: team || d.team_name,
      nationality: 'Unknown',
      tactical_style: (d.tactical_style || 'balanced') as TacticalStyle,
      formation: '4-3-3',
      inferred: false,
      history: [],
      form: calcForm(d.last_5_games)
    }
  }

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
