import torch
import torch.nn as nn
import torch.nn.functional as F

class PlayerEncoder(nn.Module):
    def __init__(self, num_player_features=10, hidden_dim=64):
        super().__init__()
        self.fc = nn.Linear(num_player_features, hidden_dim)
        self.relu = nn.ReLU()
    
    def forward(self, x):
        # x: [Batch, 11, num_player_features]
        return self.relu(self.fc(x))

class TeammateAttention(nn.Module):
    """
    Self-attention layer so each player 'understands' who they are playing with.
    """
    def __init__(self, hidden_dim=64):
        super().__init__()
        self.mha = nn.MultiheadAttention(embed_dim=hidden_dim, num_heads=4, batch_first=True)
        self.norm = nn.LayerNorm(hidden_dim)
        
    def forward(self, player_embeddings):
        # player_embeddings: [Batch, 11, hidden_dim]
        attn_output, _ = self.mha(player_embeddings, player_embeddings, player_embeddings)
        out = self.norm(player_embeddings + attn_output)
        return out

class LineupMatchModel(nn.Module):
    def __init__(self, 
                 num_player_features=10, 
                 num_manager_features=5, 
                 hidden_dim=64, 
                 num_player_outputs=5, # e.g. tackles, passes, shots, goals, assists
                 num_match_outputs=3): # Home, Draw, Away
        super().__init__()
        
        self.player_encoder = PlayerEncoder(num_player_features, hidden_dim)
        self.manager_encoder = nn.Linear(num_manager_features, hidden_dim)
        
        # Self-attention for squad synergy
        self.home_synergy = TeammateAttention(hidden_dim)
        self.away_synergy = TeammateAttention(hidden_dim)
        
        # Player-level prediction heads (Shared across all players)
        # Predicts player outcomes (tackles, goals, etc.) based on their synergy-aware embedding
        self.player_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_player_outputs)
        )
        
        # Match-level prediction head
        # We pool the 11 players + 1 manager for each team
        self.match_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 4, hidden_dim * 2), # (HomePool + HomeMgr + AwayPool + AwayMgr)
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_match_outputs)
        )

    def forward(self, 
                home_players, away_players, 
                home_manager, away_manager):
        """
        home_players: [Batch, 11, num_player_features]
        away_players: [Batch, 11, num_player_features]
        home_manager: [Batch, num_manager_features]
        away_manager: [Batch, num_manager_features]
        """
        # 1. Encode Players
        h_emb = self.player_encoder(home_players) # [B, 11, H]
        a_emb = self.player_encoder(away_players) # [B, 11, H]
        
        # 2. Synergy (Teammate Attention)
        # Allows players to adjust based on who they are playing with
        h_syn = self.home_synergy(h_emb) # [B, 11, H]
        a_syn = self.away_synergy(a_emb) # [B, 11, H]
        
        # 3. Player-Level Predictions (Multi-task output 1)
        # Predict individual stats: tackles, goals, etc.
        h_player_preds = self.player_predictor(h_syn) # [B, 11, num_player_outputs]
        a_player_preds = self.player_predictor(a_syn) # [B, 11, num_player_outputs]
        
        # 4. Encode Managers
        h_mgr_emb = F.relu(self.manager_encoder(home_manager)) # [B, H]
        a_mgr_emb = F.relu(self.manager_encoder(away_manager)) # [B, H]
        
        # 5. Pool Team Vectors (Average over the 11 players)
        h_pool = torch.mean(h_syn, dim=1) # [B, H]
        a_pool = torch.mean(a_syn, dim=1) # [B, H]
        
        # 6. Match Prediction (Multi-task output 2)
        # Combine everything to predict game outcome
        match_features = torch.cat([h_pool, h_mgr_emb, a_pool, a_mgr_emb], dim=1) # [B, H*4]
        match_preds = self.match_predictor(match_features) # [B, 3] (logits for Home/Draw/Away)
        
        return match_preds, h_player_preds, a_player_preds

if __name__ == "__main__":
    # Quick Test
    B = 2
    H_P = torch.randn(B, 11, 10)
    A_P = torch.randn(B, 11, 10)
    H_M = torch.randn(B, 5)
    A_M = torch.randn(B, 5)
    
    model = LineupMatchModel()
    m_out, hp_out, ap_out = model(H_P, A_P, H_M, A_M)
    print("Match Output Shape:", m_out.shape)
    print("Home Players Output Shape:", hp_out.shape)
    print("Away Players Output Shape:", ap_out.shape)
