import os
from datetime import date, datetime
from typing import Any

import psycopg2
from dotenv import load_dotenv

from src.managers.seed_data import CURRENT_MANAGERS_2025, MANAGER_PROFILES, TACTICAL_STYLES

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

STYLE_TO_SCORE = {style: index / (len(TACTICAL_STYLES) - 1) for index, style in enumerate(TACTICAL_STYLES)}


class ManagerRepository:
    def __init__(self):
        self.conn = psycopg2.connect(LOCAL_DB_URL)
        self._team_ids: dict[str, str] = {}
        self._tenures: list[dict[str, Any]] = []
        self._loaded = False

    def close(self):
        self.conn.close()

    def _load_cache(self):
        if self._loaded:
            return

        with self.conn.cursor() as cur:
            cur.execute("SELECT id, team_name FROM teams")
            for team_id, team_name in cur.fetchall():
                self._team_ids[team_name] = str(team_id)

            cur.execute(
                """
                SELECT m.name, m.nationality, m.tactical_style, m.preferred_formation,
                       t.team_name, mt.start_date, mt.end_date, mt.is_current
                FROM manager_tenures mt
                JOIN managers m ON mt.manager_id = m.id
                JOIN teams t ON mt.team_id = t.id
                ORDER BY mt.start_date ASC
                """
            )
            for row in cur.fetchall():
                self._tenures.append(
                    {
                        "manager_name": row[0],
                        "nationality": row[1],
                        "tactical_style": row[2] or "balanced",
                        "formation": row[3] or "4-3-3",
                        "team_name": row[4],
                        "start_date": row[5],
                        "end_date": row[6],
                        "is_current": row[7],
                    }
                )

        self._loaded = True

    def resolve_manager(self, team_name: str, match_date: date | str | None = None) -> dict[str, Any]:
        self._load_cache()
        match_day = self._as_date(match_date) if match_date else date.today()

        for tenure in reversed(self._tenures):
            if tenure["team_name"] != team_name:
                continue
            start = self._as_date(tenure["start_date"])
            end = self._as_date(tenure["end_date"]) if tenure["end_date"] else None
            if start <= match_day and (end is None or match_day <= end):
                return self._profile_from_tenure(tenure)

        fallback_name = CURRENT_MANAGERS_2025.get(team_name, "League Average")
        return self._profile_from_name(fallback_name, team_name, inferred=True)

    def get_current_manager(self, team_name: str) -> dict[str, Any]:
        self._load_cache()

        for tenure in reversed(self._tenures):
            if tenure["team_name"] == team_name and tenure["is_current"]:
                return self._profile_from_tenure(tenure)

        with self.conn.cursor() as cur:
            cur.execute("SELECT manager_name FROM teams WHERE team_name = %s", (team_name,))
            row = cur.fetchone()
            if row and row[0]:
                return self._profile_from_name(row[0], team_name, inferred=False)

        fallback_name = CURRENT_MANAGERS_2025.get(team_name, "League Average")
        return self._profile_from_name(fallback_name, team_name, inferred=True)

    def lookup_match_managers(self, home_team: str, away_team: str) -> dict[str, Any]:
        home_manager = self.get_current_manager(home_team)
        away_manager = self.get_current_manager(away_team)
        return {
            "home": {
                **home_manager,
                "history": self.get_manager_history(home_manager["name"]),
                "form": self.compute_manager_form(home_manager["name"], home_team, date.today()),
            },
            "away": {
                **away_manager,
                "history": self.get_manager_history(away_manager["name"]),
                "form": self.compute_manager_form(away_manager["name"], away_team, date.today()),
            },
        }

    def get_profile(self, manager_name: str) -> dict[str, Any]:
        profile = self._profile_from_name(manager_name, "Unknown")
        return {
            **profile,
            "history": self.get_manager_history(manager_name),
        }

    def get_manager_history(self, manager_name: str, limit: int = 8) -> list[dict[str, Any]]:
        self._load_cache()
        history = []
        for tenure in self._tenures:
            if tenure["manager_name"] != manager_name:
                continue
            history.append(
                {
                    "team": tenure["team_name"],
                    "start_date": self._as_date(tenure["start_date"]).isoformat(),
                    "end_date": tenure["end_date"].isoformat() if tenure["end_date"] else None,
                    "is_current": tenure["is_current"],
                }
            )
        return history[-limit:]

    def compute_manager_form(self, manager_name: str, team_name: str, before_date: date | str) -> dict[str, float]:
        before = self._as_date(before_date)
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.home_goals, m.away_goals, th.team_name, ta.team_name, m.match_date
                FROM match_records m
                JOIN teams th ON m.home_team_id = th.id
                JOIN teams ta ON m.away_team_id = ta.id
                WHERE m.match_date < %s
                  AND m.home_goals IS NOT NULL
                  AND m.away_goals IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT 400
                """,
                (before,),
            )
            rows = cur.fetchall()

        points = 0
        wins = 0
        played = 0
        for home_goals, away_goals, home_team, away_team, match_day in rows:
            manager_team = self.resolve_manager(home_team, match_day)["name"]
            if manager_team != manager_name:
                manager_team = self.resolve_manager(away_team, match_day)["name"]
                if manager_team != manager_name:
                    continue

            played += 1
            managed_home = manager_team == self.resolve_manager(home_team, match_day)["name"]
            if managed_home:
                if home_goals > away_goals:
                    points += 3
                    wins += 1
                elif home_goals == away_goals:
                    points += 1
            else:
                if away_goals > home_goals:
                    points += 3
                    wins += 1
                elif away_goals == home_goals:
                    points += 1

            if played >= 20:
                break

        if played == 0:
            return {"ppg": 1.3, "win_rate": 0.33, "matches": 0}

        return {
            "ppg": round(points / played, 2),
            "win_rate": round(wins / played, 2),
            "matches": played,
        }

    def compute_head_to_head(self, home_manager: str, away_manager: str, before_date: date | str) -> dict[str, float]:
        before = self._as_date(before_date)
        home_wins = 0
        away_wins = 0
        draws = 0

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT m.home_goals, m.away_goals, th.team_name, ta.team_name, m.match_date
                FROM match_records m
                JOIN teams th ON m.home_team_id = th.id
                JOIN teams ta ON m.away_team_id = ta.id
                WHERE m.match_date < %s
                  AND m.home_goals IS NOT NULL
                  AND m.away_goals IS NOT NULL
                ORDER BY m.match_date DESC
                LIMIT 800
                """,
                (before,),
            )
            rows = cur.fetchall()

        for home_goals, away_goals, home_team, away_team, match_day in rows:
            home_mgr = self.resolve_manager(home_team, match_day)["name"]
            away_mgr = self.resolve_manager(away_team, match_day)["name"]
            if home_mgr != home_manager or away_mgr != away_manager:
                continue

            if home_goals == away_goals:
                draws += 1
            elif home_goals > away_goals:
                home_wins += 1
            else:
                away_wins += 1

        total = home_wins + away_wins + draws
        return {
            "meetings": total,
            "home_manager_wins": home_wins,
            "away_manager_wins": away_wins,
            "draws": draws,
        }

    def build_feature_vector(
        self,
        home_team: str,
        away_team: str,
        home_manager: str | None = None,
        away_manager: str | None = None,
        match_date: date | str | None = None,
    ) -> dict[str, float]:
        match_day = self._as_date(match_date) if match_date else date.today()
        home_profile = self._profile_from_name(home_manager, home_team) if home_manager else self.resolve_manager(home_team, match_day)
        away_profile = self._profile_from_name(away_manager, away_team) if away_manager else self.resolve_manager(away_team, match_day)

        home_form = self.compute_manager_form(home_profile["name"], home_team, match_day)
        away_form = self.compute_manager_form(away_profile["name"], away_team, match_day)
        h2h = self.compute_head_to_head(home_profile["name"], away_profile["name"], match_day)

        home_style = STYLE_TO_SCORE.get(home_profile["tactical_style"], 0.5)
        away_style = STYLE_TO_SCORE.get(away_profile["tactical_style"], 0.5)

        return {
            "h_mgr_ppg": home_form["ppg"],
            "a_mgr_ppg": away_form["ppg"],
            "mgr_ppg_diff": home_form["ppg"] - away_form["ppg"],
            "h_mgr_win_rate": home_form["win_rate"],
            "a_mgr_win_rate": away_form["win_rate"],
            "mgr_win_rate_diff": home_form["win_rate"] - away_form["win_rate"],
            "h_mgr_style": home_style,
            "a_mgr_style": away_style,
            "mgr_style_diff": home_style - away_style,
            "mgr_h2h_meetings": h2h["meetings"],
            "mgr_h2h_home_wins": h2h["home_manager_wins"],
            "mgr_h2h_away_wins": h2h["away_manager_wins"],
        }

    def _profile_from_tenure(self, tenure: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": tenure["manager_name"],
            "team": tenure["team_name"],
            "nationality": tenure["nationality"] or "Unknown",
            "tactical_style": tenure["tactical_style"] or "balanced",
            "formation": tenure["formation"] or "4-3-3",
            "inferred": False,
        }

    def _profile_from_name(self, manager_name: str, team_name: str, inferred: bool = False) -> dict[str, Any]:
        profile = MANAGER_PROFILES.get(manager_name, MANAGER_PROFILES["League Average"])
        return {
            "name": manager_name,
            "team": team_name,
            "nationality": profile["nationality"],
            "tactical_style": profile["tactical_style"],
            "formation": profile["formation"],
            "inferred": inferred,
        }

    @staticmethod
    def _as_date(value: date | str | datetime) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
