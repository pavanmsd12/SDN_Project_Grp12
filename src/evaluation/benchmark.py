"""
Benchmark Orchestrator:
Runs all 6 algorithms through identical multi-epoch simulation runs with
realistic traffic patterns, unexpected bursts, and varying Digital Twin desynchronization.
Logs detailed operational metrics for the 12 evaluation plots.
"""

import time
import json
import numpy as np
import os

from src.network.topology import get_abilene_topology
from src.network.traffic import TrafficGenerator
from src.network.simulator import PhysicalNetworkSimulator
from src.digital_twin.twin import NetworkDigitalTwin
from src.predictor.conformal import ConformalCalibrator
from src.optimization.paths import CandidatePathGenerator
from src.optimization.fidro_mpc import FiDRO_MPC_Optimizer
from src.optimization.exact_milp import ExactMILPOptimizer
from src.baselines.reactive_te import ReactiveTE_Optimizer
from src.baselines.deterministic_mpc import DeterministicMPC_Optimizer
from src.baselines.graph_ppo import GraphPPO_Optimizer
from src.baselines.uncalibrated_dr import Uncalibrated_DR_Optimizer

def run_comprehensive_benchmark(total_epochs=20, output_path="outputs/benchmark_results.json"):
    print("=" * 60)
    print("Initializing SDN Digital-Twin Benchmark Suite (6 Algorithms)")
    print("=" * 60)

    # 1. Setup Topology & Candidate Paths
    G, link_map = get_abilene_topology()
    traffic_gen = TrafficGenerator(num_nodes=12, num_flows=16, seed=42)
    path_gen = CandidatePathGenerator(G, k1=2, k2=1, k3=1)
    flows = traffic_gen.flows

    algo_names = [
        "FiDRO-MPC",
        "Reactive-TE",
        "Deterministic-MPC",
        "Graph-PPO",
        "Uncalibrated-DR",
        "EXACT-MILP"
    ]

    # Metrics container
    results = {
        name: {
            "max_utilization": [],
            "mean_delay": [],
            "p95_delay": [],
            "packet_loss": [],
            "route_churn": [],
            "runtime_ms": [],
            "twin_fidelity": [],
            "uncertainty_radius": [],
            "sla_violations": []
        }
        for name in algo_names
    }

    # Pre-generate candidate paths for all flows
    candidate_paths = path_gen.generate_candidate_paths(flows, link_map=link_map)

    # Run each algorithm over identical traffic traces
    for algo_name in algo_names:
        print(f"\nEvaluating Algorithm: [{algo_name}] ...")
        # Instantiate simulator, twin, and optimizer
        sim = PhysicalNetworkSimulator(G, link_map)
        twin = NetworkDigitalTwin(num_links=len(link_map), kappa=3.0)
        conformal = ConformalCalibrator()

        # Optimizer selection
        if algo_name == "FiDRO-MPC":
            opt = FiDRO_MPC_Optimizer(G, link_map, horizon=3)
        elif algo_name == "Reactive-TE":
            opt = ReactiveTE_Optimizer(G, link_map, threshold=0.80)
        elif algo_name == "Deterministic-MPC":
            opt = DeterministicMPC_Optimizer(G, link_map, horizon=3)
        elif algo_name == "Graph-PPO":
            opt = GraphPPO_Optimizer(G, link_map)
        elif algo_name == "Uncalibrated-DR":
            opt = Uncalibrated_DR_Optimizer(G, link_map, horizon=3)
        elif algo_name == "EXACT-MILP":
            opt = ExactMILPOptimizer(G, link_map)

        # Initialize routes to primary shortest path
        current_routes = {f.flow_id: candidate_paths[f.flow_id][0] for f in flows}
        sim.apply_routing(current_routes)

        for t in range(total_epochs):
            # Introduce controlled traffic bursts at epochs 7-9 and 14-16 to test robustness
            burst_fids = [2, 5, 8] if (7 <= t <= 9 or 14 <= t <= 16) else []
            demands = traffic_gen.generate_demands(t, burst_flow_ids=burst_fids, burst_factor=2.3)

            # Introduce telemetry lag/noise into the Digital Twin at epochs 10-15
            twin_lag = 0.55 if (10 <= t <= 15) else 0.05

            # Step 1: Physical simulation step with current routes
            telemetry, flow_metrics, link_loads = sim.step(demands)

            # Step 2: Digital Twin synchronization & Fidelity assessment
            link_phi, global_phi, _ = twin.synchronize(telemetry, lag_factor=twin_lag)
            wasserstein_r = conformal.compute_wasserstein_radius(global_phi)

            # Step 3: Multi-scenario predictions for horizon H
            # Generates nominal, high-burst, and low scenarios
            scenarios = [
                {fid: demands[fid] * (1.0 + 0.05 * h) for fid in demands}
                for h in range(1, 4)
            ]
            # Adverse burst scenario
            scenarios.append({fid: demands[fid] * 1.35 for fid in demands})

            # Step 4: Run Optimizer and measure decision latency
            start_time = time.perf_counter()
            if algo_name == "FiDRO-MPC":
                new_routes = opt.solve(candidate_paths, current_routes, scenarios, wasserstein_r, global_phi)
            elif algo_name == "Reactive-TE":
                new_routes = opt.solve(candidate_paths, current_routes, telemetry)
            elif algo_name == "Deterministic-MPC":
                new_routes = opt.solve(candidate_paths, current_routes, scenarios[0])
            elif algo_name == "Graph-PPO":
                new_routes = opt.solve(candidate_paths, current_routes, telemetry, demands)
            elif algo_name == "Uncalibrated-DR":
                new_routes = opt.solve(candidate_paths, current_routes, scenarios)
            elif algo_name == "EXACT-MILP":
                new_routes = opt.solve(candidate_paths, current_routes, demands)

            runtime_ms = (time.perf_counter() - start_time) * 1000.0

            # Step 5: Receding-horizon execution: apply chosen routes to physical network
            churn, _ = sim.apply_routing(new_routes)
            current_routes = new_routes

            # Step 6: Log metrics
            max_u = float(np.max(link_loads / sim.capacities))
            delays = [m["delay"] for m in flow_metrics.values()]
            losses = [m["loss"] for m in flow_metrics.values()]
            sla_breaches = sum(1 for fid, m in flow_metrics.items() if m["delay"] > next(f.max_delay for f in flows if f.flow_id == fid))

            results[algo_name]["max_utilization"].append(max_u)
            results[algo_name]["mean_delay"].append(float(np.mean(delays)))
            results[algo_name]["p95_delay"].append(float(np.percentile(delays, 95)))
            results[algo_name]["packet_loss"].append(float(np.mean(losses)))
            results[algo_name]["route_churn"].append(churn)
            results[algo_name]["runtime_ms"].append(runtime_ms)
            results[algo_name]["twin_fidelity"].append(global_phi)
            results[algo_name]["uncertainty_radius"].append(wasserstein_r)
            results[algo_name]["sla_violations"].append(sla_breaches)

        print(f"Finished {algo_name}: Avg Util = {np.mean(results[algo_name]['max_utilization']):.2f}, "
              f"Mean Delay = {np.mean(results[algo_name]['mean_delay']):.2f}ms, "
              f"Total Churn = {sum(results[algo_name]['route_churn'])}, "
              f"Avg Runtime = {np.mean(results[algo_name]['runtime_ms']):.1f}ms")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nAll benchmark simulations completed! Results saved to: {output_path}")
    return results

if __name__ == "__main__":
    run_comprehensive_benchmark(total_epochs=20)
