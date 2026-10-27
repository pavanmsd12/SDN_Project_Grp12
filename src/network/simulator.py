"""
Physical Network Simulator:
Simulates packet forwarding, link queuing dynamics (M/M/1-inspired),
end-to-end latency, packet loss, and telemetry generation.
"""

import numpy as np

class PhysicalNetworkSimulator:
    def __init__(self, topology, link_map, safe_util=0.80):
        self.G = topology
        self.link_map = link_map  # (u, v) -> link_id
        self.rev_link_map = {v: k for k, v in link_map.items()}
        self.num_links = len(link_map)
        self.safe_util = safe_util

        # Link physical properties
        self.capacities = np.zeros(self.num_links, dtype=np.float32)
        self.prop_delays = np.zeros(self.num_links, dtype=np.float32)

        for (u, v), lid in self.link_map.items():
            self.capacities[lid] = self.G[u][v]["capacity"]
            self.prop_delays[lid] = self.G[u][v]["prop_delay"]

        # Current state
        self.current_routes = {}  # flow_id -> current path (list of edges or path index)
        self.prev_routes = {}

    def apply_routing(self, flow_paths):
        """
        Installs new routing decisions into physical switches (FlowMod).
        flow_paths: dict of flow_id -> path (list of (u, v) edges)
        Returns:
            churn_count: number of flows whose routes changed
            churn_dict: {flow_id: 1 if changed else 0}
        """
        self.prev_routes = dict(self.current_routes)
        churn_count = 0
        churn_dict = {}

        for fid, path in flow_paths.items():
            if fid in self.prev_routes and self.prev_routes[fid] != path:
                churn_count += 1
                churn_dict[fid] = 1
            else:
                churn_dict[fid] = 0
            self.current_routes[fid] = path

        return churn_count, churn_dict

    def step(self, demands):
        """
        Simulates network physics for the current epoch under applied routes and demands.
        Returns:
            telemetry: {lid: [util, queue_occ, delay, loss, cap]}
            flow_metrics: {fid: {"delay": ms, "loss": rate, "sla_violation": bool}}
            link_loads: np.array of load per link in Mbps
        """
        link_loads = np.zeros(self.num_links, dtype=np.float32)

        # 1. Accumulate load on links
        for fid, path in self.current_routes.items():
            demand = demands.get(fid, 0.0)
            for edge in path:
                lid = self.link_map[edge]
                link_loads[lid] += demand

        # 2. Compute link metrics
        link_utils = link_loads / (self.capacities + 1e-6)
        link_delays = np.zeros(self.num_links, dtype=np.float32)
        link_losses = np.zeros(self.num_links, dtype=np.float32)
        queue_occupancy = np.zeros(self.num_links, dtype=np.float32)

        for lid in range(self.num_links):
            cap = self.capacities[lid]
            load = link_loads[lid]
            prop = self.prop_delays[lid]

            # M/M/1 queuing approximation with buffer cap
            if load < 0.98 * cap:
                # Normal queuing: D = Dprop + 1 / (mu - lambda)
                # where mu = cap / packet_size; for 1500 byte packets, 1 Mbps ~ 83.3 pkts/s
                mu_lambda_diff = max(cap - load, 5.0)
                queuing_delay = (1000.0 / mu_lambda_diff) * 0.08  # scaled to ms
                queue_occ = load / cap
                loss = 0.0
            else:
                # Severe congestion / buffer saturation
                queuing_delay = 50.0 + (load - cap) * 0.2  # severe queuing latency
                queue_occ = 1.0
                excess = max(0.0, load - cap)
                loss = min(0.35, excess / (load + 1e-5))  # packet drop probability

            link_delays[lid] = prop + queuing_delay
            link_losses[lid] = loss
            queue_occupancy[lid] = min(1.0, queue_occ)

        # 3. Assemble telemetry vector s_e(t) = [u_e, q_e, d_e, l_e, C_e]
        telemetry = {}
        for lid in range(self.num_links):
            telemetry[lid] = np.array([
                link_utils[lid],
                queue_occupancy[lid],
                link_delays[lid],
                link_losses[lid],
                self.capacities[lid]
            ], dtype=np.float32)

        # 4. Compute end-to-end flow performance
        flow_metrics = {}
        for fid, path in self.current_routes.items():
            e2e_delay = sum(link_delays[self.link_map[edge]] for edge in path)
            # End-to-end success prob = prod(1 - loss_e)
            success_prob = 1.0
            for edge in path:
                success_prob *= (1.0 - link_losses[self.link_map[edge]])
            e2e_loss = 1.0 - success_prob

            flow_metrics[fid] = {
                "delay": float(e2e_delay),
                "loss": float(e2e_loss),
                "util_max": float(max(link_utils[self.link_map[edge]] for edge in path))
            }

        return telemetry, flow_metrics, link_loads
