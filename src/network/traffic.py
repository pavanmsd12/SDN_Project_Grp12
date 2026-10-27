"""
Traffic Generator Module:
Generates realistic dynamic traffic demands between ingress-egress node pairs.
Includes diurnal variations, Gaussian fluctuations, and sudden traffic bursts.
Each flow is defined as: f = (id, src, dst, demand_mbps, max_delay_ms, max_loss_rate).
"""

import numpy as np

class Flow:
    def __init__(self, flow_id, src, dst, base_demand=50.0, max_delay=60.0, max_loss=0.01):
        self.flow_id = flow_id
        self.src = src
        self.dst = dst
        self.base_demand = base_demand  # in Mbps
        self.max_delay = max_delay      # SLA limit in ms
        self.max_loss = max_loss        # SLA limit (e.g. 1%)
        self.current_demand = base_demand

    def __repr__(self):
        return f"Flow(id={self.flow_id}, {self.src}->{self.dst}, req={self.current_demand:.1f}M, SLA={self.max_delay}ms)"


class TrafficGenerator:
    def __init__(self, num_nodes=12, num_flows=18, seed=42):
        self.num_nodes = num_nodes
        self.num_flows = num_flows
        self.rng = np.random.RandomState(seed)
        self.flows = self._init_flows()

    def _init_flows(self):
        flows = []
        flow_id = 0
        # Select representative source-destination pairs spanning across the continent
        pairs = [
            (0, 5), (0, 4), (0, 8),   # NY to West/South (LA, Sunnyvale, Houston)
            (1, 4), (1, 5), (1, 9),   # Chicago to Sunnyvale, LA, Atlanta
            (2, 3), (2, 5), (2, 8),   # DC to Seattle, LA, Houston
            (3, 8), (3, 9), (3, 0),   # Seattle to Houston, Atlanta, NY
            (4, 0), (4, 1), (4, 9),   # Sunnyvale to NY, Chicago, Atlanta
            (5, 0), (5, 1), (5, 2),   # LA to NY, Chicago, DC
        ]

        for src, dst in pairs[:self.num_flows]:
            # Baseline demand between 60 Mbps and 180 Mbps
            base_demand = float(self.rng.uniform(70.0, 160.0))
            # Delay SLA: 45ms to 85ms depending on geographic span
            sla_delay = float(self.rng.uniform(50.0, 90.0))
            flows.append(Flow(flow_id, src, dst, base_demand, max_delay=sla_delay, max_loss=0.01))
            flow_id += 1

        return flows

    def generate_demands(self, t, burst_flow_ids=None, burst_factor=2.2):
        """
        Generates traffic demands for control epoch t.
        demands = base * diurnal_factor + noise (+ burst if targeted)
        """
        demands = {}
        # Diurnal wave (smooth 24-epoch sinusoidal cycle)
        diurnal = 1.0 + 0.35 * np.sin(2 * np.pi * t / 24.0)

        for flow in self.flows:
            # Gaussian random noise (±10%)
            noise = self.rng.normal(0, 0.08)
            d = flow.base_demand * (diurnal + noise)

            # Apply targeted sudden bursts to trigger proactive/reactive TE
            if burst_flow_ids and flow.flow_id in burst_flow_ids:
                d *= burst_factor

            flow.current_demand = max(10.0, float(d))
            demands[flow.flow_id] = flow.current_demand

        return demands
