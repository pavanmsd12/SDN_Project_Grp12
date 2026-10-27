"""
Baseline 2: Deterministic Digital-Twin MPC
Uses the same prediction model and lookahead horizon as FiDRO-MPC,
but optimizes strictly against the point mean forecast without uncertainty or fidelity calibration.
"""

import pulp
import numpy as np

class DeterministicMPC_Optimizer:
    def __init__(self, topology, link_map, horizon=3, safe_util=0.85):
        self.G = topology
        self.link_map = link_map
        self.num_links = len(link_map)
        self.horizon = horizon
        self.safe_util = safe_util
        self.capacities = np.array([self.G[u][v]["capacity"] for (u, v) in self.link_map.keys()], dtype=np.float32)
        self.prop_delays = np.array([self.G[u][v]["prop_delay"] for (u, v) in self.link_map.keys()], dtype=np.float32)

    def solve(self, candidate_paths, current_routes, mean_predicted_demands):
        """
        Solves MPC against point forecast with zero uncertainty buffer (epsilon = 0).
        """
        prob = pulp.LpProblem("Deterministic_MPC", pulp.LpMinimize)

        x_vars = {}
        for fid, paths in candidate_paths.items():
            for p_idx in range(len(paths)):
                for h in range(1, self.horizon + 1):
                    x_vars[(fid, p_idx, h)] = pulp.LpVariable(
                        f"det_x_{fid}_{p_idx}_{h}",
                        cat="Binary" if h == 1 else "Continuous",
                        lowBound=0.0, upBound=1.0
                    )

        u_peak_vars = {h: pulp.LpVariable(f"u_peak_{h}", lowBound=0.0) for h in range(1, self.horizon + 1)}

        # 1. Single path per flow per epoch
        for fid, paths in candidate_paths.items():
            for h in range(1, self.horizon + 1):
                prob += pulp.lpSum([x_vars[(fid, p_idx, h)] for p_idx in range(len(paths))]) == 1.0

        # 2. Objective: Delay + Peak utilization under mean forecast
        obj_terms = []
        for h in range(1, self.horizon + 1):
            delay_terms = []
            for fid, paths in candidate_paths.items():
                for p_idx, path in enumerate(paths):
                    p_delay = sum(self.prop_delays[self.link_map[e]] for e in path)
                    delay_terms.append(x_vars[(fid, p_idx, h)] * p_delay)

            # Link utilization under mean prediction
            for lid in range(self.num_links):
                link_traffic = []
                for fid, paths in candidate_paths.items():
                    dem = mean_predicted_demands.get(fid, 50.0)
                    for p_idx, path in enumerate(paths):
                        if lid in [self.link_map[e] for e in path]:
                            link_traffic.append(x_vars[(fid, p_idx, h)] * dem)
                prob += u_peak_vars[h] >= pulp.lpSum(link_traffic) / (self.capacities[lid] + 1e-4)

            obj_terms.append(
                0.4 * (pulp.lpSum(delay_terms) / len(candidate_paths)) +
                0.6 * u_peak_vars[h] * 50.0
            )

        prob += pulp.lpSum(obj_terms)
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=5))

        selected = {}
        for fid, paths in candidate_paths.items():
            best_p = 0
            best_val = -1.0
            for p_idx in range(len(paths)):
                val = pulp.value(x_vars[(fid, p_idx, 1)])
                if val is not None and val > best_val:
                    best_val = val
                    best_p = p_idx
            selected[fid] = paths[best_p]

        return selected
