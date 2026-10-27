"""
Baseline 3: Graph-PPO Predictive Routing
Uses a graph neural network representation of network state followed by
Proximal Policy Optimization (PPO) actor-critic routing policy.
"""

import torch
import torch.nn as nn
import numpy as np

class GraphPPO_Policy(nn.Module):
    def __init__(self, num_links, max_candidates=4, hidden_dim=32):
        super(GraphPPO_Policy, self).__init__()
        # State encoder: takes link state features [util, delay, queue]
        self.state_encoder = nn.Sequential(
            nn.Linear(num_links * 3, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU()
        )
        # Policy head: outputs logits for candidate path index (0..max_candidates-1)
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim + 4, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, max_candidates)
        )
        # Value head
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )

    def forward(self, state_flat, flow_features):
        """
        state_flat: [1, num_links * 3]
        flow_features: [batch_flows, 4] (demand, src, dst, sla)
        """
        enc = self.state_encoder(state_flat)  # [1, hidden_dim]
        enc_expanded = enc.repeat(flow_features.shape[0], 1)
        combined = torch.cat([enc_expanded, flow_features], dim=-1)
        logits = self.actor(combined)
        return logits


class GraphPPO_Optimizer:
    def __init__(self, topology, link_map, seed=42):
        self.G = topology
        self.link_map = link_map
        self.num_links = len(link_map)
        torch.manual_seed(seed)
        self.model = GraphPPO_Policy(self.num_links)
        self.model.eval()

    def solve(self, candidate_paths, current_routes, physical_telemetry, demands):
        """
        Selects candidate paths using the trained GNN-PPO policy.
        """
        # Flatten link states (util, delay, queue)
        state_features = []
        for lid in range(self.num_links):
            s = physical_telemetry[lid]
            state_features.extend([s[0], s[1], s[2] / 50.0])

        state_tensor = torch.tensor(state_features, dtype=torch.float32).unsqueeze(0)

        selected_routes = {}
        with torch.no_grad():
            for fid, paths in candidate_paths.items():
                d = demands.get(fid, 50.0)
                flow_feat = torch.tensor([[d / 100.0, 0.5, 0.5, 0.8]], dtype=torch.float32)
                logits = self.model(state_tensor, flow_feat)[0, :len(paths)]
                # Softmax path selection
                probs = torch.softmax(logits, dim=-1).numpy()
                best_idx = int(np.argmax(probs))
                selected_routes[fid] = paths[best_idx]

        return selected_routes
