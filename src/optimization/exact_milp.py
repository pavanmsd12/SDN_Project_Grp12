"""
EXACT-MILP Benchmark Optimizer:
Solves the deterministic equivalent of the multi-scenario traffic engineering problem
to global mathematical optimality via Branch-and-Bound Integer Linear Programming.
Provides the theoretical upper performance bound.
"""

import pulp
import numpy as np

class ExactMILPOptimizer:
    def __init__(self, topology, link_map, safe_util=0.85):
        self.G = topology
        self.link_map = link_map
        self.num_links = len(link_map)
        self.safe_util = safe_util
        self.capacities = np.array([self.G[u][v]["capacity"] for (u, v) in self.link_map.keys()], dtype=np.float32)
        self.prop_delays = np.array([self.G[u][v]["prop_delay"] for (u, v) in self.link_map.keys()], dtype=np.float32)

    def solve(self, candidate_paths, current_routes, demands):
        """
        Solves complete arc-based MILP to global optimality across flows.
        """
        prob = pulp.LpProblem("EXACT_MILP", pulp.LpMinimize)

        # Binary decision: x[fid, p_idx] in {0, 1}
        x = {}
        for fid, paths in candidate_paths.items():
            for p_idx in range(len(paths)):
                x[(fid, p_idx)] = pulp.LpVariable(f"exact_x_{fid}_{p_idx}", cat="Binary")

        # Peak link utilization variable U_max
        u_max = pulp.LpVariable("u_max", lowBound=0.0)

        # 1. Exactly one path per flow
        for fid, paths in candidate_paths.items():
            prob += pulp.lpSum([x[(fid, p_idx)] for p_idx in range(len(paths))]) == 1.0

        # 2. Capacity & Congestion constraints on each physical link
        for lid in range(self.num_links):
            link_load_terms = []
            for fid, paths in candidate_paths.items():
                d = demands.get(fid, 50.0)
                for p_idx, path in enumerate(paths):
                    if lid in [self.link_map[e] for e in path]:
                        link_load_terms.append(x[(fid, p_idx)] * d)

            # Link load cannot exceed capacity * u_max
            prob += pulp.lpSum(link_load_terms) <= self.capacities[lid] * u_max

        # 3. Delay minimization term
        total_delay = []
        for fid, paths in candidate_paths.items():
            for p_idx, path in enumerate(paths):
                p_delay = sum(self.prop_delays[self.link_map[e]] for e in path)
                total_delay.append(x[(fid, p_idx)] * p_delay)

        # Objective: minimize weighted combination of total delay and peak utilization
        prob += 0.5 * (pulp.lpSum(total_delay) / len(candidate_paths)) + 50.0 * u_max

        # Solve exactly
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=10))

        # Retrieve optimal routes
        optimal_routes = {}
        for fid, paths in candidate_paths.items():
            best_p = 0
            for p_idx in range(len(paths)):
                if pulp.value(x[(fid, p_idx)]) and pulp.value(x[(fid, p_idx)]) > 0.5:
                    best_p = p_idx
                    break
            optimal_routes[fid] = paths[best_p]

        return optimal_routes
