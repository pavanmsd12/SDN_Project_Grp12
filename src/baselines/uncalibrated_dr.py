"""
Baseline 4: Uncalibrated Distributionally Robust MPC (Standard DR-MPC)
Employs a robust uncertainty set, but uses a fixed, static radius epsilon_0
and completely ignores whether the Digital Twin is in-sync or lagging (beta_phi = 0).
"""

from src.optimization.fidro_mpc import FiDRO_MPC_Optimizer

class Uncalibrated_DR_Optimizer:
    def __init__(self, topology, link_map, horizon=3, fixed_radius=0.10):
        # Wraps the MPC optimizer with a fixed uncertainty radius
        self.optimizer = FiDRO_MPC_Optimizer(topology, link_map, horizon=horizon)
        self.fixed_radius = fixed_radius

    def solve(self, candidate_paths, current_routes, predicted_scenarios):
        """
        Solves DR-MPC assuming constant uncertainty radius and ignoring twin fidelity.
        """
        # Global fidelity is ignored (set statically to 1.0) and fixed radius is used
        return self.optimizer.solve(
            candidate_paths=candidate_paths,
            current_routes=current_routes,
            predicted_demands_scenarios=predicted_scenarios,
            wasserstein_radius=self.fixed_radius,
            global_fidelity=1.0  # uncalibrated: treats twin as always perfect
        )
