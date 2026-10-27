"""
Digital Twin Engine:
Maintains virtual network state s_tilde(t), simulates telemetry synchronization latency,
computes twin discrepancy delta_e(t), link fidelity phi_e(t), and global fidelity Phi(t).
"""

import numpy as np

class NetworkDigitalTwin:
    def __init__(self, num_links, kappa=3.0, desync_rate=0.0):
        self.num_links = num_links
        self.kappa = kappa              # sensitivity factor for fidelity decay
        self.desync_rate = desync_rate  # degree of telemetry lag/noise (0 = perfect, 1 = severely lagging)

        # Dimension normalization constants R_k for [util, queue, delay_ms, loss_rate, cap_mbps]
        self.R = np.array([1.0, 1.0, 50.0, 0.10, 1000.0], dtype=np.float32)
        # Component weights omega_k (sum to 1)
        self.omega = np.array([0.35, 0.20, 0.25, 0.15, 0.05], dtype=np.float32)

        # Virtual state s_tilde
        self.virtual_state = {lid: np.zeros(5, dtype=np.float32) for lid in range(num_links)}
        self.prev_telemetry = None

    def synchronize(self, physical_telemetry, lag_factor=None):
        """
        Synchronizes virtual twin with incoming physical telemetry s(t).
        lag_factor: controls the degree of twin lag (overrides self.desync_rate if provided).
        """
        lag = self.desync_rate if lag_factor is None else lag_factor
        link_fidelities = {}
        link_discrepancies = {}

        for lid, s_real in physical_telemetry.items():
            if self.prev_telemetry is None or lag == 0.0:
                # Perfect or initial synchronization
                s_virtual = s_real.copy()
            else:
                # Lagging update: exponential smoothing + stale telemetry delay
                # Higher lag means virtual twin reflects older state + sensor drift
                s_prev = self.virtual_state[lid]
                alpha = max(0.05, 1.0 - lag)
                noise = np.random.normal(0, lag * 0.15, size=s_real.shape)
                s_virtual = alpha * s_real + (1.0 - alpha) * s_prev + noise
                s_virtual = np.maximum(s_virtual, 0.0)

            self.virtual_state[lid] = s_virtual

            # Compute normalized twin discrepancy delta_e(t) (Eq. from PDF Section B)
            diff = np.abs(s_real - s_virtual)
            delta_e = np.sum(self.omega * (diff / (self.R + 1e-5)))
            link_discrepancies[lid] = float(delta_e)

            # Compute link fidelity phi_e(t) = exp(-kappa * delta_e)
            phi_e = float(np.exp(-self.kappa * delta_e))
            link_fidelities[lid] = max(0.01, min(1.0, phi_e))

        # Compute global network fidelity Phi(t) = sum_e nu_e * phi_e
        # Weights nu_e proportional to link utilization (traffic carried)
        utils = np.array([physical_telemetry[lid][0] for lid in range(self.num_links)])
        total_util = np.sum(utils) + 1e-6
        nu = utils / total_util

        phi_array = np.array([link_fidelities[lid] for lid in range(self.num_links)])
        global_fidelity = float(np.sum(nu * phi_array))

        self.prev_telemetry = physical_telemetry
        return link_fidelities, global_fidelity, link_discrepancies

    def counterfactual_evaluate(self, candidate_routes, candidate_demands, capacities):
        """
        Counterfactual evaluation inside Digital Twin:
        Simulates: 'What would link utilization be if we install candidate_routes?'
        rho_e = (sum_f A_ep * lambda_f) / C_e
        """
        predicted_loads = np.zeros(self.num_links, dtype=np.float32)
        for fid, path in candidate_routes.items():
            dem = candidate_demands.get(fid, 0.0)
            for edge_lid in path:
                predicted_loads[edge_lid] += dem

        predicted_utils = predicted_loads / (capacities + 1e-5)
        return predicted_loads, predicted_utils
