import asyncio
from src.feature_store.batch_generate import FeatureStoreBatchGenerator
from src.models.xgboost_tower import XGBoostTower
from src.models.contextual_tower import ContextualTowerTrainer
from src.models.ensemble import FPredictEnsemble

def run_ensemble_training():
    print("--- PHASE 1: REFRESHING FEATURE STORE ---")
    FeatureStoreBatchGenerator().generate_all()
    
    print("\n--- PHASE 2: TRAINING TOWER A (XGBOOST) ---")
    tower_a = XGBoostTower()
    tower_a.train()
    
    print("\n--- PHASE 3: TRAINING TOWER B (DNN) ---")
    tower_b_trainer = ContextualTowerTrainer()
    tower_b_trainer.train()
    
    print("\n--- PHASE 4: TRAINING META-LEARNER ---")
    ensemble = FPredictEnsemble(tower_a_model=tower_a, tower_b_model=tower_b_trainer.model)
    
    # Load data for meta-learner (using the same data structure as models)
    X_b, y = tower_b_trainer.load_data()
    # We need features_a in DataFrame format for XGBoost
    X_a_df, _ = tower_a.load_training_data()
    
    # We only train meta-learner on the validation portion to avoid leakage
    # For this script, we'll use a subset
    ensemble.train_meta_learner(X_a_df, X_b, y)
    print("Two-Tower Ensemble Fused and Operational.")

if __name__ == "__main__":
    run_ensemble_training()
