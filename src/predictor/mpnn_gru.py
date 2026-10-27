"""
MPNN-GRU Neural Predictor:
Topology-aware multi-step traffic predictor using graph message passing and GRU temporal units.
Outputs multi-step predictions and pinball quantiles (tau in {0.05, 0.50, 0.95}) for horizon H.
"""

import torch
import torch.nn as nn
import numpy as np

class MPNN_GRU_Predictor(nn.Module):
    def __init__(self, in_features=5, hidden_dim=32, horizon=4):
        super(MPNN_GRU_Predictor, self).__init__()
        self.horizon = horizon
        self.hidden_dim = hidden_dim

        # Initial link feature embedding: h_e^(0) = W_x * s_e(t)
        self.embedding = nn.Linear(in_features, hidden_dim)

        # Message Passing Layer: spatial propagation across neighboring links
        self.msg_weight = nn.Linear(hidden_dim, hidden_dim)
        self.self_weight = nn.Linear(hidden_dim, hidden_dim)

        # GRU Temporal Layer: g_e(t) = GRU(h_e(t), g_e(t-1))
        self.gru = nn.GRU(hidden_dim, hidden_dim, batch_first=True)

        # Multi-quantile output heads: predicts [mean, q0.05, q0.50, q0.95] for each step h in 1..H
        # Output shape: [batch, horizon, 4]
        self.decoder = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, horizon * 4)
        )

    def forward(self, x, adj_matrix):
        """
        x: [num_links, seq_len, in_features]
        adj_matrix: [num_links, num_links] adjacency matrix representing link neighborhood
        """
        num_links, seq_len, in_feat = x.shape
        x_flat = x.view(-1, in_feat)
        h = torch.relu(self.embedding(x_flat))
        h = h.view(num_links, seq_len, self.hidden_dim)

        # Spatial message passing for each time step
        spatial_out = []
        for s in range(seq_len):
            h_s = h[:, s, :]  # [num_links, hidden_dim]
            msg = torch.matmul(adj_matrix, self.msg_weight(h_s))
            h_next = torch.relu(self.self_weight(h_s) + msg)
            spatial_out.append(h_next.unsqueeze(1))

        h_spatial = torch.cat(spatial_out, dim=1)  # [num_links, seq_len, hidden_dim]

        # Temporal GRU
        gru_out, _ = self.gru(h_spatial)
        last_hidden = gru_out[:, -1, :]  # [num_links, hidden_dim]

        # Multi-step quantile decoding
        decoded = self.decoder(last_hidden)  # [num_links, horizon * 4]
        decoded = decoded.view(num_links, self.horizon, 4)

        # Separate mean, q0.05, q0.50, q0.95
        # Enforce quantile ordering: q0.05 <= q0.50 <= q0.95 via softplus offsets
        mu = decoded[:, :, 0]
        q_mid = decoded[:, :, 1]
        q_low = q_mid - torch.nn.functional.softplus(decoded[:, :, 2])
        q_high = q_mid + torch.nn.functional.softplus(decoded[:, :, 3])

        return mu, q_low, q_mid, q_high


def pinball_loss(y_true, y_pred, tau):
    """Pinball (quantile) loss for quantile regression."""
    diff = y_true - y_pred
    return torch.max((tau - 1.0) * diff, tau * diff).mean()


def train_toy_predictor(predictor, num_links, epochs=15):
    """
    Lightweight training loop to initialize realistic weights on synthetic traffic history.
    Takes < 3 seconds on modern CPU.
    """
    optimizer = torch.optim.Adam(predictor.parameters(), lr=0.01)
    adj = torch.eye(num_links)  # simplified adjacency for link graph

    for _ in range(epochs):
        optimizer.zero_grad()
        dummy_x = torch.rand(num_links, 5, 5) * 100.0
        dummy_y = torch.rand(num_links, predictor.horizon) * 120.0

        mu, q_low, q_mid, q_high = predictor(dummy_x, adj)
        loss_mse = nn.functional.mse_loss(mu, dummy_y)
        loss_q = pinball_loss(dummy_y, q_low, 0.05) + \
                 pinball_loss(dummy_y, q_mid, 0.50) + \
                 pinball_loss(dummy_y, q_high, 0.95)

        loss = loss_mse + loss_q
        loss.backward()
        optimizer.step()
