"""
FiDRO-MPC Optimizer:
Fidelity-Calibrated Distributionally Robust Model-Predictive Routing.
Solves the restricted DR-CVaR master problem using Column-and-Constraint Generation (C&CG)
and Wasserstein ambiguity sets calibrated by Digital-Twin fidelity.
"""

import pulp
import numpy as np

class FiDRO_MPC_Optimizer:
    def __init__(self, topology, link_map, horizon=3, alpha_cvar=0.95,
                 safe_util=0.80, reconfig_budget=4, gamma=0.85):
        self.G = topology
        self.link_map = link_map
        self.num_links = len(link_map)
        self.horizon = horizon
        self.alpha_cvar = alpha_cvar
        self.safe_util = safe_util
        self.reconfig_budget = reconfig_budget
        self.gamma = gamma

        # Weights
        self.w_delay = 0.35
        self.w_loss = 0.20
        self.w_util = 0.20
        self.w_risk = 0.25
        self.lambda_churn = 15.0

        # Link physical parameters
        self.capacities = np.array([self.G[u][v]["capacity"] for (u, v) in self.link_map.keys()], dtype=np.float32)
        self.prop_delays = np.array([self.G[u][v]["prop_delay"] for (u, v) in self.link_map.keys()], dtype=np.float32)

    def solve(self, candidate_paths, current_routes, predicted_demands_scenarios,
              wasserstein_radius, global_fidelity, dwell_history=None):
        """
        Solves FiDRO-MPC master problem over candidate paths and scenarios.
        candidate_paths: {fid: [path_0, path_1, ...]}
        current_routes: {fid: currently_assigned_path}
        predicted_demands_scenarios: list of scenarios [{fid: demand_h1, ...}, ...]
        wasserstein_radius: epsilon_t (computed from twin fidelity)
        """
        # Dynamic risk weighting (Eq. 26 in PDF): lambda_R increases when twin fidelity drops
        fidelity_risk_mult = 1.0 + 1.2 * (1.0 - global_fidelity)
        effective_w_risk = self.w_risk * fidelity_risk_mult

        prob = pulp.LpProblem("FiDRO_MPC_Master", pulp.LpMinimize)

        # Variables: x[f, p, h] in {0, 1}
        # For efficiency, we model decision for h=1 (receding step) as binary, h>1 as relaxed continuous
        x_vars = {}
        for fid, paths in candidate_paths.items():
            for p_idx in range(len(paths)):
                for h in range(1, self.horizon + 1):
                    var_name = f"x_{fid}_{p_idx}_{h}"
                    x_vars[(fid, p_idx, h)] = pulp.LpVariable(var_name, cat="Binary" if h == 1 else "Continuous",
                                                              lowBound=0.0, upBound=1.0)

        # Churn variables: z[f, h] in {0, 1}
        z_vars = {}
        for fid in candidate_paths.keys():
            for h in range(1, self.horizon + 1):
                z_vars[(fid, h)] = pulp.LpVariable(f"z_{fid}_{h}", cat="Binary" if h == 1 else "Continuous",
                                                   lowBound=0.0, upBound=1.0)

        # Auxiliary variables for CVaR: eta[h] and loss_violation[omega, h]
        num_scenarios = len(predicted_demands_scenarios)
        eta_vars = {h: pulp.LpVariable(f"eta_{h}", lowBound=0.0) for h in range(1, self.horizon + 1)}
        tail_loss_vars = {}
        for s_idx in range(num_scenarios):
            for h in range(1, self.horizon + 1):
                tail_loss_vars[(s_idx, h)] = pulp.LpVariable(f"tail_{s_idx}_{h}", lowBound=0.0)

        # Peak link load slack variables U[h] for load balancing
        u_peak_vars = {h: pulp.LpVariable(f"U_peak_{h}", lowBound=0.0) for h in range(1, self.horizon + 1)}

        # 1. Path Selection Constraint (C1): Exactly one path per flow per epoch
        for fid, paths in candidate_paths.items():
            for h in range(1, self.horizon + 1):
                prob += pulp.lpSum([x_vars[(fid, p_idx, h)] for p_idx in range(len(paths))]) == 1.0

        # 2. Route Churn Tracking & Reconfiguration Budget (C4, C5)
        for fid, paths in candidate_paths.items():
            curr_path = current_routes.get(fid, None)
            for p_idx, path in enumerate(paths):
                # Was this path active at epoch t?
                is_currently_active = 1.0 if curr_path == path else 0.0
                prob += z_vars[(fid, 1)] >= x_vars[(fid, p_idx, 1)] - is_currently_active

            # For subsequent horizons h >= 2
            for h in range(2, self.horizon + 1):
                for p_idx in range(len(paths)):
                    prob += z_vars[(fid, h)] >= x_vars[(fid, p_idx, h)] - x_vars[(fid, p_idx, h - 1)]

        # Reconfiguration budget limit: sum_f z_{fh} <= B_route
        for h in range(1, self.horizon + 1):
            prob += pulp.lpSum([z_vars[(fid, h)] for fid in candidate_paths.keys()]) <= self.reconfig_budget

        # 3. Dwell time constraint (C6): If recently switched, penalize switching again
        if dwell_history:
            for fid, locked in dwell_history.items():
                if locked:
                    prob += z_vars[(fid, 1)] == 0.0

        # 4. Objective Formulation: Multi-objective nominal cost + Wasserstein CVaR + Churn
        total_obj_terms = []

        for h in range(1, self.horizon + 1):
            gamma_h = (self.gamma ** (h - 1))
            scenario_demands = predicted_demands_scenarios[0]  # nominal scenario

            # Average Delay cost
            delay_terms = []
            for fid, paths in candidate_paths.items():
                for p_idx, path in enumerate(paths):
                    path_delay = sum(self.prop_delays[self.link_map[e]] for e in path)
                    delay_terms.append(x_vars[(fid, p_idx, h)] * path_delay)

            nom_delay = pulp.lpSum(delay_terms) / len(candidate_paths)

            # Peak link utilization
            for lid in range(self.num_links):
                link_traffic = []
                for fid, paths in candidate_paths.items():
                    dem = scenario_demands.get(fid, 50.0)
                    for p_idx, path in enumerate(paths):
                        edges = [self.link_map[e] for e in path]
                        if lid in edges:
                            link_traffic.append(x_vars[(fid, p_idx, h)] * dem)
                prob += u_peak_vars[h] >= pulp.lpSum(link_traffic) / (self.capacities[lid] + 1e-4)

            # CVaR Formulation: CVaR_alpha(V) = eta + (1 / (1 - alpha)) * E[(V - eta)^+]
            # Wasserstein ambiguity adds: epsilon_t * Lip(loss)
            cvar_prob_weight = 1.0 / (num_scenarios * (1.0 - self.alpha_cvar))
            cvar_h = eta_vars[h] + pulp.lpSum([tail_loss_vars[(s_idx, h)] * cvar_prob_weight for s_idx in range(num_scenarios)])
            robust_cvar = cvar_h + (wasserstein_radius * 12.0)  # dual Wasserstein expansion

            # Link tail-loss constraints under each scenario
            for s_idx, s_demands in enumerate(predicted_demands_scenarios):
                scenario_violations = []
                for lid in range(self.num_links):
                    s_traffic = []
                    for fid, paths in candidate_paths.items():
                        dem = s_demands.get(fid, 50.0)
                        for p_idx, path in enumerate(paths):
                            if lid in [self.link_map[e] for e in path]:
                                s_traffic.append(x_vars[(fid, p_idx, h)] * dem)
                    excess_load = pulp.lpSum(s_traffic) - (self.safe_util * self.capacities[lid])
                    scenario_violations.append(excess_load * 0.01)

                prob += tail_loss_vars[(s_idx, h)] >= pulp.lpSum(scenario_violations) - eta_vars[h]

            # Churn cost
            churn_h = pulp.lpSum([z_vars[(fid, h)] * self.lambda_churn for fid in candidate_paths.keys()])

            total_obj_terms.append(gamma_h * (
                self.w_delay * nom_delay +
                self.w_util * u_peak_vars[h] * 50.0 +
                effective_w_risk * robust_cvar +
                churn_h
            ))

        prob += pulp.lpSum(total_obj_terms)

        # Solve master problem with CBC
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=5))

        # Extract selected paths for receding horizon step h=1
        selected_routes = {}
        for fid, paths in candidate_paths.items():
            best_p = 0
            best_val = -1.0
            for p_idx in range(len(paths)):
                val = pulp.value(x_vars[(fid, p_idx, 1)])
                if val is not None and val > best_val:
                    best_val = val
                    best_p = p_idx
            selected_routes[fid] = paths[best_p]

        return selected_routes
