from datetime import date

import pandas as pd

from src.models.ensemble import FPredictEngine
from src.models.manager_tower import ManagerTower
from src.managers.repository import ManagerRepository


class ManagerPredictionEngine:
    BASE_WEIGHT = 0.68
    MANAGER_WEIGHT = 0.32

    def __init__(self):
        self.base_engine = FPredictEngine()
        self.manager_repo = ManagerRepository()
        self.manager_tower = ManagerTower()
        try:
            self.manager_tower.load_model()
            self.manager_ready = True
        except Exception:
            self.manager_ready = False

    def close(self):
        self.manager_repo.close()
        self.manager_tower.close()

    def lookup_managers(self, home_team: str, away_team: str):
        home_manager = self.manager_repo.get_current_manager(home_team)
        away_manager = self.manager_repo.get_current_manager(away_team)
        return {
            "home": {
                **home_manager,
                "history": self.manager_repo.get_manager_history(home_manager["name"]),
                "form": self.manager_repo.compute_manager_form(home_manager["name"], home_team, date.today()),
            },
            "away": {
                **away_manager,
                "history": self.manager_repo.get_manager_history(away_manager["name"]),
                "form": self.manager_repo.compute_manager_form(away_manager["name"], away_team, date.today()),
            },
        }

    def predict(
        self,
        home_team: str,
        away_team: str,
        home_features: dict,
        away_features: dict,
        odds: list[float],
        home_manager_name: str | None = None,
        away_manager_name: str | None = None,
    ):
        features_a_dict = {
            "h_elo": home_features["elo"],
            "h_squad_power": home_features["power"],
            "h_sdi": home_features["sdi"],
            "h_form_ppg": home_features["form"],
            "h_form_gd": home_features["gd"],
            "h_sentiment": home_features["sent"],
            "a_elo": away_features["elo"],
            "a_squad_power": away_features["power"],
            "a_sdi": away_features["sdi"],
            "a_form_ppg": away_features["form"],
            "a_form_gd": away_features["gd"],
            "a_sentiment": away_features["sent"],
            "odds_home": odds[0],
            "odds_draw": odds[1],
            "odds_away": odds[2],
            "elo_diff": home_features["elo"] - away_features["elo"],
            "form_diff": home_features["form"] - away_features["form"],
            "gd_diff": home_features["gd"] - away_features["gd"],
            "sentiment_diff": home_features["sent"] - away_features["sent"],
            "match_month": float(date.today().month),
        }
        features_a_df = pd.DataFrame([features_a_dict])
        features_b = [
            [
                home_features["elo"],
                home_features["power"],
                home_features["sdi"],
                home_features["form"],
                home_features["gd"],
                home_features["sent"],
                away_features["elo"],
                away_features["power"],
                away_features["sdi"],
                away_features["form"],
                away_features["gd"],
                away_features["sent"],
                odds[0],
                odds[1],
                odds[2],
                float(date.today().month),
            ]
        ]

        base_probs = self.base_engine.ensemble.predict(features_a_df, features_b)
        managers = self.lookup_managers(home_team, away_team)

        if home_manager_name:
            managers["home"] = {
                **self.manager_repo._profile_from_name(home_manager_name, home_team),
                "history": self.manager_repo.get_manager_history(home_manager_name),
                "form": self.manager_repo.compute_manager_form(home_manager_name, home_team, date.today()),
            }
        if away_manager_name:
            managers["away"] = {
                **self.manager_repo._profile_from_name(away_manager_name, away_team),
                "history": self.manager_repo.get_manager_history(away_manager_name),
                "form": self.manager_repo.compute_manager_form(away_manager_name, away_team, date.today()),
            }

        manager_features = self.manager_repo.build_feature_vector(
            home_team,
            away_team,
            home_manager_name or managers["home"]["name"],
            away_manager_name or managers["away"]["name"],
        )
        h2h = self.manager_repo.compute_head_to_head(
            managers["home"]["name"],
            managers["away"]["name"],
            date.today(),
        )

        if self.manager_ready:
            manager_probs = self.manager_tower.predict_proba(manager_features)
            blended = (
                self.BASE_WEIGHT * base_probs[0] + self.MANAGER_WEIGHT * manager_probs[0],
                self.BASE_WEIGHT * base_probs[1] + self.MANAGER_WEIGHT * manager_probs[1],
                self.BASE_WEIGHT * base_probs[2] + self.MANAGER_WEIGHT * manager_probs[2],
            )
            total = sum(blended)
            final_probs = tuple(value / total for value in blended)
        else:
            manager_probs = base_probs
            final_probs = base_probs

        value_bets = self.base_engine.trade_recommendation(
            home_team,
            away_team,
            odds[0],
            odds[1],
            odds[2],
            features_a_df,
            features_b,
        )

        return {
            "home": final_probs[2] * 100,
            "draw": final_probs[1] * 100,
            "away": final_probs[0] * 100,
            "base_probs": {
                "home": base_probs[2] * 100,
                "draw": base_probs[1] * 100,
                "away": base_probs[0] * 100,
            },
            "manager_probs": {
                "home": manager_probs[2] * 100,
                "draw": manager_probs[1] * 100,
                "away": manager_probs[0] * 100,
            },
            "manager_factor": {
                "weight": self.MANAGER_WEIGHT,
                "features": manager_features,
                "head_to_head": h2h,
            },
            "managers": managers,
            "value_bets": value_bets,
        }
