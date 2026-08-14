"""
Fantasy Premier League guidance engine.

Uses player impact metrics and team fixture difficulty when DB data is available,
with a curated fallback pool for offline / pre-sync scenarios.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import psycopg2
from dotenv import load_dotenv

load_dotenv()

BUDGET = 100.0
SQUAD_SIZE = 15
MAX_PER_TEAM = 3
POSITION_SLOTS = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
STARTING_FORMATION = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}

# Season starts mid-August; GW1 ≈ Aug 15
SEASON_START = date(2026, 8, 15)

ACTIVE_EPL_TEAMS = {
    "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton & Hove Albion",
    "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town",
    "Leicester City", "Liverpool", "Manchester City", "Manchester United",
    "Newcastle United", "Nottingham Forest", "Southampton", "Tottenham Hotspur",
    "West Ham United", "Wolverhampton Wanderers", "Wolves",
    "Leeds United", "Sunderland", "Coventry City", "Hull City",
    "Man City", "Man United", "Nott'm Forest", "Brighton", "Spurs",
}


@dataclass
class FantasyPlayer:
    id: str
    name: str
    team: str
    position: str
    price: float
    projected_points: float
    next_fixture: str
    fixture_difficulty: int  # 1 (easy) – 5 (hard)
    form: str
    is_injured: bool = False
    ownership: float = 0.0

    @property
    def value(self) -> float:
        return self.projected_points / max(self.price, 4.0)


FALLBACK_PLAYERS: list[dict[str, Any]] = [
    {"name": "Erling Haaland", "team": "Manchester City", "position": "FWD", "price": 14.5, "base": 8.2, "form": "Excellent"},
    {"name": "Mohamed Salah", "team": "Liverpool", "position": "FWD", "price": 14.0, "base": 7.8, "form": "Excellent"},
    {"name": "Bukayo Saka", "team": "Arsenal", "position": "MID", "price": 10.0, "base": 6.5, "form": "Good"},
    {"name": "Cole Palmer", "team": "Chelsea", "position": "MID", "price": 10.5, "base": 6.8, "form": "Excellent"},
    {"name": "Martin Ødegaard", "team": "Arsenal", "position": "MID", "price": 8.0, "base": 5.8, "form": "Good"},
    {"name": "Phil Foden", "team": "Manchester City", "position": "MID", "price": 8.5, "base": 6.2, "form": "Excellent"},
    {"name": "Ollie Watkins", "team": "Aston Villa", "position": "FWD", "price": 8.5, "base": 5.5, "form": "Good"},
    {"name": "Alexander Isak", "team": "Newcastle United", "position": "FWD", "price": 10.5, "base": 6.0, "form": "Good"},
    {"name": "Dominic Solanke", "team": "Tottenham Hotspur", "position": "FWD", "price": 7.5, "base": 5.2, "form": "Good"},
    {"name": "Jarrod Bowen", "team": "West Ham United", "position": "MID", "price": 8.0, "base": 5.4, "form": "Average"},
    {"name": "Bruno Fernandes", "team": "Manchester United", "position": "MID", "price": 9.0, "base": 5.8, "form": "Good"},
    {"name": "Rodri", "team": "Manchester City", "position": "MID", "price": 6.5, "base": 4.8, "form": "Excellent"},
    {"name": "Declan Rice", "team": "Arsenal", "position": "MID", "price": 6.5, "base": 4.5, "form": "Good"},
    {"name": "Trent Alexander-Arnold", "team": "Liverpool", "position": "DEF", "price": 7.0, "base": 5.5, "form": "Good"},
    {"name": "William Saliba", "team": "Arsenal", "position": "DEF", "price": 6.0, "base": 4.8, "form": "Excellent"},
    {"name": "Gabriel Magalhães", "team": "Arsenal", "position": "DEF", "price": 6.0, "base": 4.6, "form": "Good"},
    {"name": "Virgil van Dijk", "team": "Liverpool", "position": "DEF", "price": 6.0, "base": 4.5, "form": "Good"},
    {"name": "Kieran Trippier", "team": "Newcastle United", "position": "DEF", "price": 5.0, "base": 4.0, "form": "Average"},
    {"name": "Pedro Porro", "team": "Tottenham Hotspur", "position": "DEF", "price": 5.5, "base": 4.3, "form": "Good"},
    {"name": "Matty Cash", "team": "Aston Villa", "position": "DEF", "price": 4.5, "base": 3.8, "form": "Good"},
    {"name": "Alisson", "team": "Liverpool", "position": "GK", "price": 5.5, "base": 4.5, "form": "Excellent"},
    {"name": "Ederson", "team": "Manchester City", "position": "GK", "price": 5.5, "base": 4.3, "form": "Good"},
    {"name": "David Raya", "team": "Arsenal", "position": "GK", "price": 5.5, "base": 4.2, "form": "Good"},
    {"name": "Emiliano Martínez", "team": "Aston Villa", "position": "GK", "price": 5.0, "base": 4.0, "form": "Good"},
    {"name": "Nick Pope", "team": "Newcastle United", "position": "GK", "price": 5.0, "base": 3.8, "form": "Average"},
    {"name": "Antoine Semenyo", "team": "Bournemouth", "position": "MID", "price": 7.0, "base": 5.0, "form": "Excellent"},
    {"name": "Evanilson", "team": "Bournemouth", "position": "FWD", "price": 7.0, "base": 4.8, "form": "Good"},
    {"name": "Jean-Philippe Mateta", "team": "Crystal Palace", "position": "FWD", "price": 7.5, "base": 5.0, "form": "Good"},
    {"name": "Morgan Gibbs-White", "team": "Nottingham Forest", "position": "MID", "price": 7.5, "base": 5.2, "form": "Good"},
    {"name": "Chris Wood", "team": "Nottingham Forest", "position": "FWD", "price": 7.5, "base": 4.9, "form": "Average"},
    {"name": "Bryan Mbeumo", "team": "Brentford", "position": "MID", "price": 8.0, "base": 5.6, "form": "Excellent"},
    {"name": "Yoane Wissa", "team": "Brentford", "position": "FWD", "price": 7.5, "base": 5.1, "form": "Good"},
    {"name": "Cole Palmer", "team": "Chelsea", "position": "MID", "price": 10.5, "base": 6.8, "form": "Excellent"},
    {"name": "Enzo Fernández", "team": "Chelsea", "position": "MID", "price": 6.5, "base": 4.4, "form": "Average"},
    {"name": "Marc Cucurella", "team": "Chelsea", "position": "DEF", "price": 5.0, "base": 3.9, "form": "Good"},
    {"name": "James Tarkowski", "team": "Everton", "position": "DEF", "price": 5.5, "base": 4.0, "form": "Good"},
    {"name": "Jordan Pickford", "team": "Everton", "position": "GK", "price": 5.0, "base": 3.7, "form": "Average"},
    {"name": "Raúl Jiménez", "team": "Fulham", "position": "FWD", "price": 6.5, "base": 4.2, "form": "Average"},
    {"name": "Alex Iwobi", "team": "Fulham", "position": "MID", "price": 6.5, "base": 4.3, "form": "Good"},
    {"name": "Kaoru Mitoma", "team": "Brighton & Hove Albion", "position": "MID", "price": 6.5, "base": 4.5, "form": "Good"},
    {"name": "Danny Welbeck", "team": "Brighton & Hove Albion", "position": "FWD", "price": 6.5, "base": 4.4, "form": "Good"},
    {"name": "Pascal Groß", "team": "Brighton & Hove Albion", "position": "MID", "price": 6.0, "base": 4.0, "form": "Average"},
    {"name": "Lewis Dunk", "team": "Brighton & Hove Albion", "position": "DEF", "price": 4.5, "base": 3.5, "form": "Average"},
    {"name": "Diogo Jota", "team": "Liverpool", "position": "FWD", "price": 7.5, "base": 5.0, "form": "Good"},
    {"name": "Luis Díaz", "team": "Liverpool", "position": "MID", "price": 8.0, "base": 5.3, "form": "Good"},
    {"name": "Kai Havertz", "team": "Arsenal", "position": "FWD", "price": 7.5, "base": 4.8, "form": "Average"},
    {"name": "Leandro Trossard", "team": "Arsenal", "position": "MID", "price": 7.0, "base": 4.6, "form": "Good"},
    {"name": "Bernardo Silva", "team": "Manchester City", "position": "MID", "price": 6.5, "base": 4.7, "form": "Good"},
    {"name": "Savinho", "team": "Manchester City", "position": "MID", "price": 7.0, "base": 4.9, "form": "Good"},
    {"name": "Marcus Rashford", "team": "Manchester United", "position": "MID", "price": 7.0, "base": 4.5, "form": "Average"},
    {"name": "Amad Diallo", "team": "Manchester United", "position": "MID", "price": 6.5, "base": 4.8, "form": "Excellent"},
    {"name": "Lisandro Martínez", "team": "Manchester United", "position": "DEF", "price": 5.0, "base": 3.6, "form": "Average"},
    {"name": "Murillo", "team": "Nottingham Forest", "position": "DEF", "price": 5.5, "base": 4.1, "form": "Good"},
    {"name": "Anthony Elanga", "team": "Nottingham Forest", "position": "MID", "price": 7.0, "base": 4.7, "form": "Good"},
    {"name": "Serge Aurier", "team": "Nottingham Forest", "position": "DEF", "price": 4.5, "base": 3.4, "form": "Average"},
    {"name": "Iliman Ndiaye", "team": "Everton", "position": "MID", "price": 6.5, "base": 4.5, "form": "Good"},
    {"name": "Beto", "team": "Everton", "position": "FWD", "price": 5.5, "base": 3.8, "form": "Average"},
    {"name": "Sander Berge", "team": "Fulham", "position": "MID", "price": 5.0, "base": 3.5, "form": "Average"},
    {"name": "Calvin Bassey", "team": "Fulham", "position": "DEF", "price": 4.5, "base": 3.4, "form": "Good"},
    {"name": "Antoine Semenyo", "team": "Bournemouth", "position": "MID", "price": 7.0, "base": 5.0, "form": "Excellent"},
    {"name": "Dean Henderson", "team": "Crystal Palace", "position": "GK", "price": 5.0, "base": 3.6, "form": "Good"},
    {"name": "Marc Guéhi", "team": "Crystal Palace", "position": "DEF", "price": 4.5, "base": 3.5, "form": "Good"},
    {"name": "Micky van de Ven", "team": "Tottenham Hotspur", "position": "DEF", "price": 4.5, "base": 3.8, "form": "Good"},
    {"name": "Guglielmo Vicario", "team": "Tottenham Hotspur", "position": "GK", "price": 5.0, "base": 3.7, "form": "Average"},
    {"name": "Dan Burn", "team": "Newcastle United", "position": "DEF", "price": 5.0, "base": 3.7, "form": "Good"},
    {"name": "Bruno Guimarães", "team": "Newcastle United", "position": "MID", "price": 6.5, "base": 4.4, "form": "Good"},
    {"name": "Trevoh Chalobah", "team": "Chelsea", "position": "DEF", "price": 5.0, "base": 3.8, "form": "Good"},
    {"name": "Robert Sánchez", "team": "Chelsea", "position": "GK", "price": 4.5, "base": 3.4, "form": "Average"},
    {"name": "Ivan Toney", "team": "Brentford", "position": "FWD", "price": 7.5, "base": 4.8, "form": "Good"},
    {"name": "Ethan Pinnock", "team": "Brentford", "position": "DEF", "price": 4.5, "base": 3.5, "form": "Average"},
    {"name": "Nico Williams", "team": "Arsenal", "position": "MID", "price": 7.0, "base": 4.7, "form": "Good"},
    {"name": "Myles Lewis-Skelly", "team": "Arsenal", "position": "DEF", "price": 5.0, "base": 3.6, "form": "Good"},
    {"name": "Jeremy Doku", "team": "Manchester City", "position": "MID", "price": 6.5, "base": 4.6, "form": "Good"},
    {"name": "Rúben Dias", "team": "Manchester City", "position": "DEF", "price": 5.5, "base": 4.0, "form": "Good"},
    {"name": "Nuno Mendes", "team": "Manchester City", "position": "DEF", "price": 5.5, "base": 3.9, "form": "Average"},
]

# Upcoming fixture difficulty by team (next 3 GWs) — opponent strength proxy
FIXTURE_RUNS: dict[str, list[tuple[str, int]]] = {
    "Manchester City": [("Wolves", 2), ("West Ham", 2), ("Fulham", 2)],
    "Arsenal": [("Leeds", 2), ("Nott'm Forest", 2), ("Newcastle", 3)],
    "Liverpool": [("Bournemouth", 2), ("Arsenal", 4), ("Burnley", 2)],
    "Chelsea": [("Crystal Palace", 2), ("West Ham", 2), ("Fulham", 2)],
    "Tottenham Hotspur": [("Burnley", 2), ("Bournemouth", 2), ("West Ham", 2)],
    "Aston Villa": [("Newcastle", 3), ("Brentford", 2), ("Everton", 2)],
    "Manchester United": [("Arsenal", 4), ("Fulham", 2), ("Burnley", 2)],
    "Newcastle United": [("Aston Villa", 3), ("Wolves", 2), ("Arsenal", 4)],
    "Brighton & Hove Albion": [("Fulham", 2), ("Everton", 2), ("Bournemouth", 2)],
    "West Ham United": [("Sunderland", 2), ("Chelsea", 3), ("Spurs", 3)],
    "Brentford": [("Nott'm Forest", 2), ("Aston Villa", 3), ("Chelsea", 3)],
    "Fulham": [("Brighton", 2), ("Man United", 2), ("Man City", 4)],
    "Crystal Palace": [("Chelsea", 3), ("Nott'm Forest", 2), ("West Ham", 2)],
    "Everton": [("Leeds", 2), ("Brighton", 2), ("Aston Villa", 3)],
    "Bournemouth": [("Liverpool", 4), ("Spurs", 3), ("Brighton", 2)],
    "Nottingham Forest": [("Brentford", 2), ("Arsenal", 4), ("Crystal Palace", 2)],
    "Leeds United": [("Everton", 2), ("Arsenal", 4), ("Wolves", 2)],
    "Sunderland": [("West Ham", 2), ("Burnley", 2), ("Wolves", 2)],
    "Ipswich Town": [("Hull", 2), ("Coventry", 2), ("Leeds", 2)],
    "Coventry City": [("Ipswich", 2), ("Hull", 2), ("Sunderland", 2)],
    "Hull City": [("Ipswich", 2), ("Coventry", 2), ("Leeds", 2)],
}

# Blank / double gameweek calendar (illustrative for chip planning)
BLANK_GAMEWEEKS = {18, 29}
DOUBLE_GAMEWEEKS = {15, 19, 34, 37}


class FantasyEngine:
    def __init__(self):
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self._team_elo: dict[str, float] = {}

    def current_gameweek(self, as_of: date | None = None) -> int:
        today = as_of or date.today()
        if today < SEASON_START:
            return 1
        days = (today - SEASON_START).days
        return min(38, max(1, (days // 7) + 1))

    def _connect(self):
        return psycopg2.connect(
            f"dbname=fpredict_db user={self.db_user} password={self.db_password} host=localhost"
        )

    def _load_team_elo(self) -> dict[str, float]:
        if self._team_elo:
            return self._team_elo
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT t.team_name,
                           COALESCE((f.features->>'elo_rating')::float, 1500)
                    FROM teams t
                    LEFT JOIN LATERAL (
                        SELECT features FROM feature_store fs
                        WHERE fs.team_id = t.id
                        ORDER BY snapshot_date DESC LIMIT 1
                    ) f ON true
                """)
                for row in cur.fetchall():
                    self._team_elo[row[0]] = float(row[1])
            conn.close()
        except Exception:
            pass
        return self._team_elo

    def _normalize_position(self, pos: str) -> str:
        pos = (pos or "MID").upper()
        if pos in ("G", "GK", "GOALKEEPER"):
            return "GK"
        if pos in ("D", "DEF", "DF", "DEFENDER"):
            return "DEF"
        if pos in ("M", "MF", "MID", "MIDFIELDER"):
            return "MID"
        if pos in ("F", "FW", "FWD", "FORWARD", "ST", "AM"):
            return "FWD"
        if "G" in pos:
            return "GK"
        if "D" in pos:
            return "DEF"
        if "F" in pos or "S" in pos:
            return "FWD"
        return "MID"

    def _fixture_multiplier(self, team: str, gw: int) -> float:
        runs = FIXTURE_RUNS.get(team, [("Average", 3), ("Average", 3), ("Average", 3)])
        idx = min(max(gw - self.current_gameweek(), 0), 2)
        difficulty = runs[idx][1]
        return {1: 1.15, 2: 1.08, 3: 1.0, 4: 0.88, 5: 0.78}.get(difficulty, 1.0)

    def _next_fixture_label(self, team: str, gw: int) -> tuple[str, int]:
        runs = FIXTURE_RUNS.get(team, [("TBC", 3)])
        idx = min(max(gw - self.current_gameweek(), 0), len(runs) - 1)
        opp, diff = runs[idx]
        home = gw % 2 == 1
        prefix = "vs" if home else "@"
        return f"{prefix} {opp}", diff

    def _players_from_db(self) -> list[FantasyPlayer] | None:
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.name, t.team_name, p.position, p.is_injured,
                           COALESCE(m.impact_score, 0.5) AS impact
                    FROM players p
                    JOIN teams t ON p.team_id = t.id
                    LEFT JOIN LATERAL (
                        SELECT impact_score FROM player_impact_metrics pim
                        WHERE pim.player_id = p.id
                        ORDER BY snapshot_date DESC LIMIT 1
                    ) m ON true
                    WHERE t.is_active = true
                """)
                rows = cur.fetchall()
            conn.close()
            if len(rows) < 30:
                return None

            gw = self.current_gameweek()
            players: list[FantasyPlayer] = []
            seen: set[str] = set()
            for idx, row in enumerate(rows):
                pid, name, team, pos, injured, impact = row
                if not name or str(name).strip().lower() in ("nan", "none", ""):
                    continue
                key = f"{name}|{team}"
                if key in seen:
                    continue
                seen.add(key)

                position = self._normalize_position(pos)
                impact_norm = min(float(impact or 0.5) / 2.5, 1.0)
                if position == "GK":
                    base_gw = 2.5 + impact_norm * 2.5
                elif position == "DEF":
                    base_gw = 2.5 + impact_norm * 3.5
                elif position == "MID":
                    base_gw = 2.5 + impact_norm * 4.5
                else:
                    base_gw = 2.5 + impact_norm * 5.5

                price = round(max(4.0, min(14.5, 4.5 + base_gw * 1.1)), 1)
                mult = self._fixture_multiplier(team, gw)
                fixture, diff = self._next_fixture_label(team, gw)
                projected = round(base_gw * mult * 22, 1)
                form = "Excellent" if impact_norm > 0.75 else "Good" if impact_norm > 0.45 else "Average"
                players.append(FantasyPlayer(
                    id=str(pid),
                    name=str(name).strip(),
                    team=team,
                    position=position,
                    price=price,
                    projected_points=projected,
                    next_fixture=fixture,
                    fixture_difficulty=diff,
                    form=form,
                    is_injured=bool(injured),
                ))

            if len(players) < 50:
                return None
            return players
        except Exception:
            return None

    def _players_from_fallback(self) -> list[FantasyPlayer]:
        gw = self.current_gameweek()
        seen: set[str] = set()
        players: list[FantasyPlayer] = []
        for idx, raw in enumerate(FALLBACK_PLAYERS):
            key = f"{raw['name']}|{raw['team']}"
            if key in seen:
                continue
            seen.add(key)
            team = raw["team"]
            mult = self._fixture_multiplier(team, gw)
            fixture, diff = self._next_fixture_label(team, gw)
            base = raw["base"]
            projected = round(base * mult * 22, 1)
            players.append(FantasyPlayer(
                id=f"fb-{idx}",
                name=raw["name"],
                team=team,
                position=raw["position"],
                price=raw["price"],
                projected_points=projected,
                next_fixture=fixture,
                fixture_difficulty=diff,
                form=raw["form"],
            ))
        return players

    def load_players(self) -> tuple[list[FantasyPlayer], str]:
        curated = self._players_from_fallback()
        db_players = self._players_from_db()
        if db_players:
            db_by_name = {p.name.lower(): p for p in db_players}
            for player in curated:
                match = db_by_name.get(player.name.lower())
                if match:
                    player.is_injured = match.is_injured
                    if match.form == "Excellent" and player.form != "Excellent":
                        player.form = "Good"
            return curated, "curated+database"
        return curated, "curated"

    def _min_fill_cost(
        self,
        available: list[FantasyPlayer],
        slots: dict[str, int],
        squad_ids: set[str],
        team_counts: dict[str, int],
    ) -> float:
        cost = 0.0
        temp_counts = dict(team_counts)
        for pos, need in slots.items():
            if need <= 0:
                continue
            candidates = sorted(
                [p for p in available if p.position == pos and p.id not in squad_ids],
                key=lambda p: p.price,
            )
            filled = 0
            for player in candidates:
                if filled >= need:
                    break
                if temp_counts.get(player.team, 0) >= MAX_PER_TEAM:
                    continue
                cost += player.price
                temp_counts[player.team] = temp_counts.get(player.team, 0) + 1
                filled += 1
            if filled < need:
                return BUDGET + 1
        return cost

    def optimize_squad(self, players: list[FantasyPlayer]) -> list[FantasyPlayer]:
        available = [p for p in players if not p.is_injured]
        squad: list[FantasyPlayer] = []
        team_counts: dict[str, int] = {}
        spent = 0.0
        slots = dict(POSITION_SLOTS)

        for pos in ("GK", "DEF", "MID", "FWD"):
            need = slots[pos]
            candidates = sorted(
                [p for p in available if p.position == pos],
                key=lambda p: p.value,
                reverse=True,
            )
            picked = 0
            for player in candidates:
                if picked >= need:
                    break
                if player in squad:
                    continue
                if team_counts.get(player.team, 0) >= MAX_PER_TEAM:
                    continue

                remaining = dict(slots)
                remaining[pos] = need - picked - 1
                reserve = self._min_fill_cost(
                    available,
                    remaining,
                    {p.id for p in squad} | {player.id},
                    team_counts,
                )
                if spent + player.price + reserve > BUDGET:
                    continue

                squad.append(player)
                picked += 1
                slots[pos] -= 1
                team_counts[player.team] = team_counts.get(player.team, 0) + 1
                spent += player.price

        # Fill any remaining slots with cheapest valid options
        for pos, need in slots.items():
            if need <= 0:
                continue
            candidates = sorted(
                [p for p in available if p.position == pos and p not in squad],
                key=lambda p: p.price,
            )
            for player in candidates:
                if need <= 0:
                    break
                if team_counts.get(player.team, 0) >= MAX_PER_TEAM:
                    continue
                if spent + player.price > BUDGET:
                    continue
                squad.append(player)
                need -= 1
                slots[pos] -= 1
                team_counts[player.team] = team_counts.get(player.team, 0) + 1
                spent += player.price

        return squad

    def pick_starting_xi(self, squad: list[FantasyPlayer]) -> dict[str, Any]:
        by_pos: dict[str, list[FantasyPlayer]] = {"GK": [], "DEF": [], "MID": [], "FWD": []}
        for p in squad:
            by_pos[p.position].append(p)

        for pos in by_pos:
            by_pos[pos].sort(key=lambda p: p.projected_points, reverse=True)

        starting: list[FantasyPlayer] = []
        for pos, count in STARTING_FORMATION.items():
            starting.extend(by_pos[pos][:count])

        bench = [p for p in squad if p not in starting]
        captain = max(starting, key=lambda p: p.projected_points)
        vice = sorted(
            [p for p in starting if p.id != captain.id],
            key=lambda p: p.projected_points,
            reverse=True,
        )[0]

        return {
            "starting_xi": starting,
            "bench": bench,
            "captain": captain,
            "vice_captain": vice,
            "formation": "4-4-2",
        }

    def suggest_transfers(
        self,
        players: list[FantasyPlayer],
        current_squad: list[FantasyPlayer] | None,
        gameweek: int,
        free_transfers: int = 1,
    ) -> dict[str, Any]:
        optimal = self.optimize_squad(players)
        baseline = current_squad or optimal

        baseline_ids = {p.id for p in baseline}
        optimal_ids = {p.id for p in optimal}

        players_out = [p for p in baseline if p.id not in optimal_ids]
        players_in = [p for p in optimal if p.id not in baseline_ids]

        # Pair by position for sensible swap suggestions
        transfers: list[dict[str, Any]] = []
        outs_by_pos: dict[str, list[FantasyPlayer]] = {}
        ins_by_pos: dict[str, list[FantasyPlayer]] = {}
        for p in players_out:
            outs_by_pos.setdefault(p.position, []).append(p)
        for p in players_in:
            ins_by_pos.setdefault(p.position, []).append(p)

        for pos in ("GK", "DEF", "MID", "FWD"):
            outs = sorted(outs_by_pos.get(pos, []), key=lambda p: p.projected_points)
            ins = sorted(ins_by_pos.get(pos, []), key=lambda p: p.projected_points, reverse=True)
            for out_p, in_p in zip(outs, ins):
                gain = round(in_p.projected_points - out_p.projected_points, 1)
                cost_delta = round(in_p.price - out_p.price, 1)
                transfers.append({
                    "out": self._player_dict(out_p),
                    "in": self._player_dict(in_p),
                    "points_gain": gain,
                    "cost_delta": cost_delta,
                    "priority": "High" if gain >= 8 else "Medium" if gain >= 4 else "Low",
                    "reason": self._transfer_reason(out_p, in_p, gameweek),
                })

        transfers.sort(key=lambda t: t["points_gain"], reverse=True)
        recommended = transfers[:free_transfers] if free_transfers else transfers[:1]
        hold = len(transfers) == 0 or (transfers and transfers[0]["points_gain"] < 3)

        watchlist = self._fixture_watchlist(players, baseline, gameweek)

        return {
            "gameweek": gameweek,
            "free_transfers": free_transfers,
            "recommended_action": "Hold" if hold else "Transfer",
            "transfers": recommended,
            "all_suggestions": transfers[:5] if transfers else watchlist[:5],
            "watchlist": watchlist[:5],
            "summary": self._transfer_summary(recommended, hold, gameweek),
        }

    def _fixture_watchlist(
        self,
        players: list[FantasyPlayer],
        squad: list[FantasyPlayer],
        gameweek: int,
    ) -> list[dict[str, Any]]:
        squad_ids = {p.id for p in squad}
        candidates = sorted(
            [p for p in players if p.id not in squad_ids and p.fixture_difficulty <= 2],
            key=lambda p: p.projected_points,
            reverse=True,
        )
        watchlist = []
        for player in candidates[:8]:
            watchlist.append({
                "out": {"name": "—", "team": "", "position": player.position, "price": 0, "projected_points": 0, "next_fixture": "", "fixture_difficulty": 0, "form": "", "id": ""},
                "in": self._player_dict(player),
                "points_gain": player.projected_points,
                "cost_delta": player.price,
                "priority": "Watch",
                "reason": f"Strong GW{gameweek} fixture ({player.next_fixture}, FDR {player.fixture_difficulty}). Consider for future transfers.",
            })
        return watchlist

    def _transfer_reason(self, out_p: FantasyPlayer, in_p: FantasyPlayer, gw: int) -> str:
        parts = []
        if in_p.fixture_difficulty <= 2 and out_p.fixture_difficulty >= 4:
            parts.append(f"{in_p.name} has a favourable run (FDR {in_p.fixture_difficulty})")
        if in_p.form == "Excellent" and out_p.form != "Excellent":
            parts.append(f"{in_p.name} is in strong form")
        if in_p.projected_points - out_p.projected_points >= 6:
            parts.append("projected points edge is significant this gameweek")
        if not parts:
            parts.append(f"Upgrade from {out_p.name} ({out_p.next_fixture}) to {in_p.name} ({in_p.next_fixture})")
        return "; ".join(parts) + "."

    def _transfer_summary(self, transfers: list[dict], hold: bool, gw: int) -> str:
        if hold:
            return f"GW{gw}: No urgent moves. Save your free transfer — fixture swings ahead may offer better value."
        names_in = ", ".join(t["in"]["name"] for t in transfers[:2])
        total_gain = sum(t["points_gain"] for t in transfers)
        return f"GW{gw}: Bring in {names_in} for an estimated +{total_gain:.1f} projected points this gameweek."

    def chip_strategy(self, players: list[FantasyPlayer], gameweek: int) -> dict[str, Any]:
        gw = gameweek
        chips = []

        # Wildcard
        if gw <= 6:
            wc_window = "Now (early season)"
            wc_rating = "High"
            wc_reason = "Build a template squad before prices rise. Fix structure issues before GW8 deadline."
        elif gw in (15, 16, 17):
            wc_window = f"GW{gw}–17"
            wc_rating = "High"
            wc_reason = "Pre-winter reset window. Rebuild before fixture congestion and before double gameweeks."
        else:
            wc_window = "Hold unless squad is broken"
            wc_rating = "Low"
            wc_reason = "Save for a major injury crisis or before a double gameweek block."

        chips.append({
            "chip": "Wildcard",
            "status": "Available",
            "recommended_window": wc_window,
            "rating": wc_rating,
            "advice": wc_reason,
        })

        # Free Hit
        if gw in BLANK_GAMEWEEKS:
            fh_rating = "High"
            fh_window = f"GW{gw} (blank gameweek)"
            fh_reason = "Many teams blank — use Free Hit to field a full XI without lasting squad damage."
        elif gw in (19, 20, 34, 35):
            fh_rating = "Medium"
            fh_window = f"GW{gw}–{gw + 1}"
            fh_reason = "Consider Free Hit to navigate a difficult fixture swing or mini-blank."
        else:
            fh_rating = "Low"
            fh_window = f"GW{min(BLANK_GAMEWEEKS)} or GW{min(DOUBLE_GAMEWEEKS)} prep"
            fh_reason = f"Save for blank GW{min(BLANK_GAMEWEEKS)} or use before a double gameweek to maximize bench."

        chips.append({
            "chip": "Free Hit",
            "status": "Available",
            "recommended_window": fh_window,
            "rating": fh_rating,
            "advice": fh_reason,
        })

        # Bench Boost
        squad = self.optimize_squad(players)
        xi = self.pick_starting_xi(squad)
        bench_pts = sum(p.projected_points for p in xi["bench"])
        if gw in DOUBLE_GAMEWEEKS and bench_pts > 25:
            bb_rating = "High"
            bb_window = f"GW{gw} (double gameweek)"
            bb_reason = f"Strong bench projected at {bench_pts:.0f} pts — Bench Boost doubles all 15 players' scores."
        else:
            bb_rating = "Medium" if bench_pts > 20 else "Low"
            bb_window = f"GW{min(DOUBLE_GAMEWEEKS)} (next double GW)"
            bb_reason = f"Wait for a double gameweek when all 15 players play twice. Current bench: {bench_pts:.0f} projected pts."

        chips.append({
            "chip": "Bench Boost",
            "status": "Available",
            "recommended_window": bb_window,
            "rating": bb_rating,
            "advice": bb_reason,
        })

        # Triple Captain
        captain_candidates = sorted(players, key=lambda p: p.projected_points, reverse=True)[:5]
        premium = captain_candidates[0]
        if gw in DOUBLE_GAMEWEEKS and premium.fixture_difficulty <= 2:
            tc_rating = "High"
            tc_window = f"GW{gw} on {premium.name}"
            tc_reason = f"{premium.name} has easy fixtures and tops projections — Triple Captain in a double GW is optimal."
        elif premium.fixture_difficulty <= 2:
            tc_rating = "Medium"
            tc_window = f"GW{gw} if {premium.name} starts"
            tc_reason = f"Single GW option on {premium.name} ({premium.next_fixture}, FDR {premium.fixture_difficulty}). Prefer double GW."
        else:
            tc_rating = "Low"
            tc_window = f"GW{min(DOUBLE_GAMEWEEKS)} double gameweek"
            tc_reason = "Hold Triple Captain for a double gameweek on a premium attacker with easy fixtures."

        chips.append({
            "chip": "Triple Captain",
            "status": "Available",
            "recommended_window": tc_window,
            "rating": tc_rating,
            "advice": tc_reason,
        })

        return {
            "gameweek": gw,
            "chips": chips,
            "priority_order": self._chip_priority(chips, gw),
            "calendar_notes": {
                "blank_gameweeks": sorted(BLANK_GAMEWEEKS),
                "double_gameweeks": sorted(DOUBLE_GAMEWEEKS),
            },
        }

    def _chip_priority(self, chips: list[dict], gw: int) -> list[str]:
        order = sorted(chips, key=lambda c: {"High": 0, "Medium": 1, "Low": 2}[c["rating"]])
        return [f"{c['chip']} ({c['rating']}) — {c['recommended_window']}" for c in order]

    def _player_dict(self, p: FantasyPlayer) -> dict[str, Any]:
        return {
            "id": p.id,
            "name": p.name,
            "team": p.team,
            "position": p.position,
            "price": p.price,
            "projected_points": p.projected_points,
            "next_fixture": p.next_fixture,
            "fixture_difficulty": p.fixture_difficulty,
            "form": p.form,
        }

    def get_guide(self, gameweek: int | None = None) -> dict[str, Any]:
        gw = gameweek or self.current_gameweek()
        players, source = self.load_players()
        squad = self.optimize_squad(players)
        xi = self.pick_starting_xi(squad)
        transfers = self.suggest_transfers(players, squad, gw)
        chips = self.chip_strategy(players, gw)

        total_cost = sum(p.price for p in squad)
        total_projected = sum(p.projected_points for p in squad)
        starting_projected = sum(p.projected_points for p in xi["starting_xi"])
        captain_bonus = xi["captain"].projected_points

        return {
            "gameweek": gw,
            "deadline": self._deadline_label(gw),
            "data_source": source,
            "budget": {
                "total": BUDGET,
                "spent": round(total_cost, 1),
                "remaining": round(BUDGET - total_cost, 1),
            },
            "best_squad": {
                "players": [self._player_dict(p) for p in squad],
                "starting_xi": [self._player_dict(p) for p in xi["starting_xi"]],
                "bench": [self._player_dict(p) for p in xi["bench"]],
                "captain": self._player_dict(xi["captain"]),
                "vice_captain": self._player_dict(xi["vice_captain"]),
                "formation": xi["formation"],
                "total_projected_points": round(total_projected, 1),
                "starting_xi_projected": round(starting_projected, 1),
                "captain_projected": round(captain_bonus, 1),
            },
            "transfers": transfers,
            "chips": chips,
            "guidance": self._weekly_guidance(gw, xi, transfers, chips),
        }

    def _deadline_label(self, gw: int) -> str:
        deadline = SEASON_START.replace(day=SEASON_START.day)
        from datetime import timedelta
        deadline = SEASON_START + timedelta(days=(gw - 1) * 7 + 5)
        return deadline.strftime("%a %d %b, 18:30")

    def _weekly_guidance(self, gw: int, xi: dict, transfers: dict, chips: dict) -> list[str]:
        tips = []
        cap = xi["captain"]
        tips.append(
            f"Captain {cap.name} ({cap.next_fixture}, FDR {cap.fixture_difficulty}) — "
            f"projected {cap.projected_points} pts."
        )
        if transfers["recommended_action"] == "Hold":
            tips.append(transfers["summary"])
        else:
            for t in transfers["transfers"][:2]:
                tips.append(f"Transfer: {t['out']['name']} → {t['in']['name']} ({t['reason']})")

        high_chips = [c for c in chips["chips"] if c["rating"] == "High"]
        if high_chips:
            tips.append(f"Chip alert: Consider {high_chips[0]['chip']} — {high_chips[0]['advice']}")

        if gw in BLANK_GAMEWEEKS:
            tips.append("Blank gameweek — prioritize players who are confirmed to play.")
        if gw in DOUBLE_GAMEWEEKS:
            tips.append("Double gameweek — load up on players with two fixtures; ideal for Bench Boost / Triple Captain.")

        return tips
