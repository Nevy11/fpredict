import torch
import torch.nn as nn
import torch.nn.functional as F

class TeammateAttention(nn.Module):
    def __init__(self, feature_dim, hidden_dim):
        super().__init__()
        self.query = nn.Linear(feature_dim, hidden_dim)
        self.key = nn.Linear(feature_dim, hidden_dim)
        self.value = nn.Linear(feature_dim, hidden_dim)
        
    def forward(self, player_features, teammate_features):
        # player_features: [B, feature_dim]
        # teammate_features: [B, 10, feature_dim]
        
        Q = self.query(player_features).unsqueeze(1) # [B, 1, hidden_dim]
        K = self.key(teammate_features) # [B, 10, hidden_dim]
        V = self.value(teammate_features) # [B, 10, hidden_dim]
        
        # Attention scores
        scores = torch.bmm(Q, K.transpose(1, 2)) / (K.size(-1) ** 0.5) # [B, 1, 10]
        attn_weights = F.softmax(scores, dim=-1)
        
        # Context vector
        context = torch.bmm(attn_weights, V).squeeze(1) # [B, hidden_dim]
        return context, attn_weights

class PlayerPerformanceModel(nn.Module):
    def __init__(self, num_player_features=5, hidden_dim=64, num_outputs=4):
        """
        Features expected (e.g., tackles, shots, dribbles, passes, xg_contribution)
        Outputs expected (e.g., predicted tackles, predicted shots, predicted dribbles, predicted passes)
        """
        super().__init__()
        self.feature_dim = num_player_features
        
        # Encoders
        self.player_encoder = nn.Linear(num_player_features, hidden_dim)
        self.teammate_encoder = nn.Linear(num_player_features, hidden_dim)
        
        # Attention to understand who they play with
        self.teammate_attention = TeammateAttention(hidden_dim, hidden_dim)
        
        # Opponent encoder (aggregate stats of the opposing team)
        self.opponent_encoder = nn.Linear(num_player_features, hidden_dim)
        
        # Fully connected layers for the final multi-task prediction
        self.fc1 = nn.Linear(hidden_dim * 3, hidden_dim * 2)
        self.fc2 = nn.Linear(hidden_dim * 2, hidden_dim)
        
        # Multi-task outputs (e.g., impact/rating, tackles, shots, passes)
        self.output_head = nn.Linear(hidden_dim, num_outputs)
        
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.2)

    def forward(self, player_x, teammates_x, opponent_x):
        """
        player_x: [B, F] - The target player's historical averages
        teammates_x: [B, 10, F] - The 10 teammates' historical averages
        opponent_x: [B, F] - The opposing team's aggregated defensive/offensive stats
        """
        # Encode inputs
        p_emb = self.relu(self.player_encoder(player_x)) # [B, H]
        
        t_emb = self.relu(self.teammate_encoder(teammates_x)) # [B, 10, H]
        
        o_emb = self.relu(self.opponent_encoder(opponent_x)) # [B, H]
        
        # Apply attention over teammates based on the player
        teammate_context, attn_weights = self.teammate_attention(p_emb, t_emb) # [B, H]
        
        # Concatenate player context, teammate context, and opponent context
        combined = torch.cat([p_emb, teammate_context, o_emb], dim=1) # [B, H*3]
        
        # Pass through dense layers
        x = self.relu(self.fc1(combined))
        x = self.dropout(x)
        x = self.relu(self.fc2(x))
        x = self.dropout(x)
        
        # Output multi-task predictions
        predictions = self.output_head(x) # [B, num_outputs]
        
        return predictions, attn_weights
