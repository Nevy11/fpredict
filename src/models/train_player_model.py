import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from player_performance_model import PlayerPerformanceModel

def generate_synthetic_data(num_samples=10000, num_features=5, num_outputs=4):
    """
    Generate synthetic data for player performance training.
    Features: [tackles, shots, dribbles, passes, xG]
    Outputs: [pred_tackles, pred_shots, pred_passes, impact_rating]
    """
    print("Generating synthetic dataset...")
    # Player historical stats
    player_x = torch.rand(num_samples, num_features) * 10
    
    # Teammate historical stats (10 teammates)
    teammates_x = torch.rand(num_samples, 10, num_features) * 10
    
    # Opponent aggregated stats
    opponent_x = torch.rand(num_samples, num_features) * 10
    
    # Target outputs based on inputs + some noise
    # e.g., if teammates have high passes, player passes might increase
    teammate_mean = teammates_x.mean(dim=1)
    
    target_tackles = player_x[:, 0] * 0.5 + opponent_x[:, 1] * 0.3 + torch.randn(num_samples)
    target_shots = player_x[:, 1] * 0.6 + teammate_mean[:, 3] * 0.2 + torch.randn(num_samples)
    target_passes = player_x[:, 3] * 0.7 + teammate_mean[:, 3] * 0.4 + torch.randn(num_samples)
    impact_rating = (target_tackles + target_shots + target_passes) / 3.0 + torch.randn(num_samples) * 0.5
    
    targets = torch.stack([target_tackles, target_shots, target_passes, impact_rating], dim=1)
    
    return TensorDataset(player_x, teammates_x, opponent_x, targets)

def train():
    print("Initializing Player Performance Model...")
    model = PlayerPerformanceModel(num_player_features=5, hidden_dim=64, num_outputs=4)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    dataset = generate_synthetic_data(num_samples=5000)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    
    epochs = 20
    print("Starting training loop...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for p_x, t_x, o_x, y in train_loader:
            optimizer.zero_grad()
            
            preds, _ = model(p_x, t_x, o_x)
            loss = criterion(preds, y)
            
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * p_x.size(0)
            
        epoch_loss = running_loss / len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for p_x, t_x, o_x, y in val_loader:
                preds, _ = model(p_x, t_x, o_x)
                loss = criterion(preds, y)
                val_loss += loss.item() * p_x.size(0)
        val_loss = val_loss / len(val_loader.dataset)
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {epoch_loss:.4f} - Val Loss: {val_loss:.4f}")
            
    # Save the trained model
    save_path = os.path.join(os.path.dirname(__file__), "player_performance.pth")
    torch.save(model.state_dict(), save_path)
    print(f"Model successfully trained and saved to {save_path}")

if __name__ == "__main__":
    train()
