import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from src.models.lineup_match_model import LineupMatchModel

def generate_synthetic_lineup_data(num_samples=10000, num_player_features=10, num_manager_features=5, num_player_outputs=5):
    """
    Generate synthetic data for 11v11 Lineup-based Match Prediction.
    """
    print("Generating synthetic 11v11 match dataset...")
    
    # 11 players per team
    home_players = torch.rand(num_samples, 11, num_player_features)
    away_players = torch.rand(num_samples, 11, num_player_features)
    
    # Managers
    home_manager = torch.rand(num_samples, num_manager_features)
    away_manager = torch.rand(num_samples, num_manager_features)
    
    # Synthetic Player Outcomes (e.g., [tackles, passes, shots, goals, assists])
    # Add some correlation with player features and teammate average
    home_player_targets = home_players[:, :, :num_player_outputs] * 1.2 + torch.randn(num_samples, 11, num_player_outputs) * 0.1
    away_player_targets = away_players[:, :, :num_player_outputs] * 1.2 + torch.randn(num_samples, 11, num_player_outputs) * 0.1
    
    # Synthetic Match Outcome (0: Away Win, 1: Draw, 2: Home Win)
    # Simple logic: higher sum of player features + manager features gives higher probability
    home_strength = home_players.sum(dim=(1,2)) + home_manager.sum(dim=1)
    away_strength = away_players.sum(dim=(1,2)) + away_manager.sum(dim=1)
    diff = home_strength - away_strength
    
    match_targets = torch.zeros(num_samples, dtype=torch.long)
    match_targets[diff > 5] = 2 # Home Win
    match_targets[(diff <= 5) & (diff >= -5)] = 1 # Draw
    match_targets[diff < -5] = 0 # Away Win

    return TensorDataset(home_players, away_players, home_manager, away_manager, 
                         home_player_targets, away_player_targets, match_targets)

def train(use_real_db=False):
    print("Initializing Lineup Match Model (Tower C)...")
    model = LineupMatchModel(
        num_player_features=5, # Updated to match DB columns (tackles, passes, shots, goals, assists)
        num_manager_features=3, # Updated to match DB columns
        hidden_dim=64, 
        num_player_outputs=5, 
        num_match_outputs=3
    )
    
    # Two losses: one for player stats (Regression), one for match outcome (Classification)
    criterion_player = nn.MSELoss()
    criterion_match = nn.CrossEntropyLoss()
    
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    if use_real_db:
        # Import dynamically to avoid circular dependencies
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from feature_store.lineup_dataset import LineupDatasetBuilder
        
        print("Using real database for training data...")
        builder = LineupDatasetBuilder()
        dataset = builder.build_dataset(num_player_features=5, num_manager_features=3)
        builder.close()
    else:
        dataset = generate_synthetic_lineup_data(num_samples=5000, num_player_features=5, num_manager_features=3, num_player_outputs=5)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    epochs = 20
    alpha = 0.5 # Weight for player loss vs match loss
    
    print("Starting training loop...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        
        for hp, ap, hm, am, hp_y, ap_y, m_y in train_loader:
            optimizer.zero_grad()
            
            # Forward pass
            match_preds, h_player_preds, a_player_preds = model(hp, ap, hm, am)
            
            # Compute losses
            loss_m = criterion_match(match_preds, m_y)
            loss_hp = criterion_player(h_player_preds, hp_y)
            loss_ap = criterion_player(a_player_preds, ap_y)
            
            # Total multi-task loss
            total_loss = loss_m + alpha * (loss_hp + loss_ap)
            
            total_loss.backward()
            optimizer.step()
            
            running_loss += total_loss.item() * hp.size(0)
            
        epoch_loss = running_loss / len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        correct = 0
        total_matches = 0
        with torch.no_grad():
            for hp, ap, hm, am, hp_y, ap_y, m_y in val_loader:
                match_preds, h_player_preds, a_player_preds = model(hp, ap, hm, am)
                
                loss_m = criterion_match(match_preds, m_y)
                loss_hp = criterion_player(h_player_preds, hp_y)
                loss_ap = criterion_player(a_player_preds, ap_y)
                
                total_loss = loss_m + alpha * (loss_hp + loss_ap)
                val_loss += total_loss.item() * hp.size(0)
                
                # Match accuracy
                _, predicted = torch.max(match_preds.data, 1)
                total_matches += m_y.size(0)
                correct += (predicted == m_y).sum().item()
                
        val_loss = val_loss / len(val_loader.dataset)
        val_acc = 100 * correct / total_matches
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs} | Train Loss: {epoch_loss:.4f} | Val Loss: {val_loss:.4f} | Val Match Acc: {val_acc:.2f}%")
            
    # Save the trained model
    save_path = os.path.join(os.path.dirname(__file__), "lineup_match_model.pth")
    torch.save(model.state_dict(), save_path)
    print(f"Model successfully trained and saved to {save_path}")

if __name__ == "__main__":
    train(use_real_db=True)
