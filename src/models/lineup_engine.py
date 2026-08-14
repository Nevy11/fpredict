import os
import torch
import psycopg2
import pandas as pd
from datetime import date

from src.models.lineup_match_model import LineupMatchModel
from src.managers.repository import ManagerRepository
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
LOCAL_DB_URL = f"dbname=fpredict_db user={DB_USER} password={DB_PASSWORD} host=localhost"

TEAM_NAME_MAPPING = {
    "Brighton & Hove Albion": "Brighton",
    "Manchester City": "Man City",
    "Manchester United": "Man United",
    "Nottingham Forest": "Nott'm Forest",
    "Tottenham Hotspur": "Tottenham",
    "Leicester City": "Leicester",
    "Leeds United": "Leeds",
    "Coventry City": "Coventry",
}

DB_TO_DISPLAY = {db: display for display, db in TEAM_NAME_MAPPING.items()}

FALLBACK_FIXTURES = [
    {"id": "fb-1", "home_team": "Manchester City", "away_team": "Arsenal", "match_date": "2026-08-21", "competition": "EPL"},
    {"id": "fb-2", "home_team": "Coventry City", "away_team": "Chelsea", "match_date": "2026-08-22", "competition": "EPL"},
    {"id": "fb-3", "home_team": "Liverpool", "away_team": "Aston Villa", "match_date": "2026-08-22", "competition": "EPL"},
    {"id": "fb-4", "home_team": "Sunderland", "away_team": "Newcastle United", "match_date": "2026-08-22", "competition": "EPL"},
    {"id": "fb-5", "home_team": "Tottenham Hotspur", "away_team": "Everton", "match_date": "2026-08-22", "competition": "EPL"},
    {"id": "fb-6", "home_team": "Manchester United", "away_team": "Leeds United", "match_date": "2026-08-23", "competition": "EPL"},
    {"id": "fb-7", "home_team": "Brighton & Hove Albion", "away_team": "Bournemouth", "match_date": "2026-08-24", "competition": "EPL"},
    {"id": "fb-8", "home_team": "Arsenal", "away_team": "Liverpool", "match_date": "2026-08-28", "competition": "EPL"},
    {"id": "fb-9", "home_team": "Chelsea", "away_team": "Manchester United", "match_date": "2026-08-29", "competition": "EPL"},
    {"id": "fb-10", "home_team": "Newcastle United", "away_team": "Manchester City", "match_date": "2026-08-29", "competition": "EPL"},
]


class LineupEngine:
    """Tower C — lineup synergy model with per-player expected outcomes."""

    def __init__(self):
        self.model = LineupMatchModel(
            num_player_features=5,
            num_manager_features=3,
            hidden_dim=64,
            num_player_outputs=5,
            num_match_outputs=3,
        )
        model_path = os.path.join(os.path.dirname(__file__), "lineup_match_model.pth")
        if os.path.exists(model_path):
            self.model.load_state_dict(torch.load(model_path, weights_only=True))
            self.model.eval()
            self.model_ready = True
        else:
            self.model_ready = False

        self.manager_repo = ManagerRepository()

    def close(self):
        self.manager_repo.close()

    @staticmethod
    def resolve_db_team_name(team_name: str) -> str:
        return TEAM_NAME_MAPPING.get(team_name, team_name)

    @staticmethod
    def resolve_display_team_name(db_name: str) -> str:
        return DB_TO_DISPLAY.get(db_name, db_name)

    def get_upcoming_fixtures(self, limit: int = 30) -> list[dict]:
        fixtures: list[dict] = []
        try:
            conn = psycopg2.connect(LOCAL_DB_URL)
            query = """
                SELECT m.id, m.match_date, m.competition,
                       th.team_name AS home_db, ta.team_name AS away_db
                FROM match_records m
                JOIN teams th ON m.home_team_id = th.id
                JOIN teams ta ON m.away_team_id = ta.id
                WHERE m.home_goals IS NULL AND m.away_goals IS NULL
                  AND m.match_date >= CURRENT_DATE
                ORDER BY m.match_date ASC
                LIMIT %s
            """
            df = pd.read_sql(query, conn, params=(limit,))
            conn.close()
            for _, row in df.iterrows():
                fixtures.append({
                    "id": str(row["id"]),
                    "home_team": self.resolve_display_team_name(row["home_db"]),
                    "away_team": self.resolve_display_team_name(row["away_db"]),
                    "match_date": row["match_date"].strftime("%Y-%m-%d")
                    if hasattr(row["match_date"], "strftime")
                    else str(row["match_date"]),
                    "competition": row["competition"] or "EPL",
                })
        except Exception:
            fixtures = []

        if not fixtures:
            return FALLBACK_FIXTURES[:limit]
        return fixtures

    def get_top_11_players(self, team_name: str) -> pd.DataFrame:
        conn = psycopg2.connect(LOCAL_DB_URL)
        query = """
            SELECT
                p.id AS player_id,
                p.name AS player_name,
                COALESCE(p.position, 'MID') AS position,
                COALESCE(pim.impact_score, 0.0) AS rating_score,
                0.0 AS xg_contribution,
                0.0 AS progressive_passes,
                0.0 AS pressing_regains,
                0.0 AS minutes_played
            FROM players p
            JOIN teams t ON t.id = p.team_id
            LEFT JOIN LATERAL (
                SELECT impact_score
                FROM player_impact_metrics
                WHERE player_id = p.id
                ORDER BY snapshot_date DESC LIMIT 1
            ) pim ON true
            WHERE t.team_name = %s
            ORDER BY pim.impact_score DESC NULLS LAST
            LIMIT 11
        """
        df = pd.read_sql(query, conn, params=(team_name,))
        conn.close()
        return df

    @staticmethod
    def _format_model_player(row, pred) -> dict:
        heuristic = LineupEngine._heuristic_player(row)
        raw_rating = float(pred[4])
        minutes = max(0, int(pred[0]))
        xg = round(float(pred[1]), 2)
        prog = max(0, int(pred[2]))
        press = max(0, int(pred[3]))

        # Untrained or out-of-range model outputs → blend with impact heuristic
        if raw_rating < 3.0 or raw_rating > 10.0 or minutes == 0:
            return heuristic

        return {
            "name": row["player_name"],
            "position": row.get("position") or "—",
            "predicted_rating": round(raw_rating, 1),
            "expected": {
                "minutes": minutes,
                "xg": xg,
                "progressive_passes": prog,
                "pressing_regains": press,
            },
        }

    @staticmethod
    def _heuristic_player(row) -> dict:
        impact = float(row.get("rating_score") or 0.0)
        norm = min(impact / 2.5, 1.0) if impact > 0 else 0.35
        return {
            "name": row["player_name"],
            "position": row.get("position") or "—",
            "predicted_rating": round(5.5 + norm * 3.0, 1),
            "expected": {
                "minutes": int(55 + norm * 35),
                "xg": round(norm * 0.45, 2),
                "progressive_passes": int(2 + norm * 8),
                "pressing_regains": int(1 + norm * 5),
            },
        }

    @staticmethod
    def _heuristic_match_probs(h_elo: float, a_elo: float) -> dict[str, float]:
        dr = (h_elo + 50) - a_elo
        p_home = 1 / (1 + 10 ** (-dr / 400))
        p_draw = 0.24
        p_home_adj = p_home * (1 - p_draw)
        p_away_adj = (1 - p_home) * (1 - p_draw)
        total = p_home_adj + p_draw + p_away_adj
        return {
            "home": round(p_home_adj / total * 100, 1),
            "draw": round(p_draw / total * 100, 1),
            "away": round(p_away_adj / total * 100, 1),
        }

    def predict(
        self,
        home_team: str,
        away_team: str,
        home_elo: float = 1500,
        away_elo: float = 1500,
    ) -> dict | None:
        db_home = self.resolve_db_team_name(home_team)
        db_away = self.resolve_db_team_name(away_team)
        display_home = home_team if home_team in TEAM_NAME_MAPPING or home_team == db_home else self.resolve_display_team_name(db_home)
        display_away = away_team if away_team in TEAM_NAME_MAPPING or away_team == db_away else self.resolve_display_team_name(db_away)

        h_df = self.get_top_11_players(db_home)
        a_df = self.get_top_11_players(db_away)

        if h_df.empty and a_df.empty:
            return None

        use_model = (
            self.model_ready
            and len(h_df) >= 11
            and len(a_df) >= 11
        )

        if use_model:
            mgr_feats = self.manager_repo.build_feature_vector(
                db_home, db_away, match_date=date.today()
            )
            h_mgr = torch.tensor(
                [[mgr_feats.get("h_mgr_ppg", 0.0), mgr_feats.get("h_mgr_win_rate", 0.0), mgr_feats.get("h_mgr_style", 0.0)]],
                dtype=torch.float32,
            )
            a_mgr = torch.tensor(
                [[mgr_feats.get("a_mgr_ppg", 0.0), mgr_feats.get("a_mgr_win_rate", 0.0), mgr_feats.get("a_mgr_style", 0.0)]],
                dtype=torch.float32,
            )
            feature_cols = [
                "minutes_played",
                "xg_contribution",
                "progressive_passes",
                "pressing_regains",
                "rating_score",
            ]
            h_tensor = torch.tensor([h_df[feature_cols].values], dtype=torch.float32)
            a_tensor = torch.tensor([a_df[feature_cols].values], dtype=torch.float32)

            with torch.no_grad():
                match_preds, h_player_preds, a_player_preds = self.model(
                    h_tensor, a_tensor, h_mgr, a_mgr
                )
            match_probs_raw = torch.nn.functional.softmax(match_preds, dim=1).numpy()[0]
            match_probs = {
                "away": round(float(match_probs_raw[0] * 100), 1),
                "draw": round(float(match_probs_raw[1] * 100), 1),
                "home": round(float(match_probs_raw[2] * 100), 1),
            }
            home_lineup = [
                self._format_model_player(h_df.iloc[i], h_player_preds[0][i].numpy())
                for i in range(len(h_df))
            ]
            away_lineup = [
                self._format_model_player(a_df.iloc[i], a_player_preds[0][i].numpy())
                for i in range(len(a_df))
            ]
            source = "tower_c_model"
        else:
            match_probs = self._heuristic_match_probs(home_elo, away_elo)
            home_lineup = [self._heuristic_player(h_df.iloc[i]) for i in range(len(h_df))]
            away_lineup = [self._heuristic_player(a_df.iloc[i]) for i in range(len(a_df))]
            source = "tower_c_heuristic"

        return {
            "home_team": display_home,
            "away_team": display_away,
            "model_ready": self.model_ready,
            "source": source,
            "lineup_complete": len(h_df) >= 11 and len(a_df) >= 11,
            "match_probs": match_probs,
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "player_predictions": {
                "home": home_lineup,
                "away": away_lineup,
            },
        }
