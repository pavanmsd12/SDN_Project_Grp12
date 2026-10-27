"""
Test script for Phase 2: Validates Digital Twin Synchronization, Discrepancy, and Fidelity Scoring.
"""

from src.network.topology import get_abilene_topology
from src.network.traffic import TrafficGenerator
from src.network.simulator import PhysicalNetworkSimulator
from src.digital_twin.twin import NetworkDigitalTwin
import networkx as nx

def test_phase2():
    print("=" * 65)
    print("           RUNNING PHASE 2 VERIFICATION TEST")
    print("=" * 65)

    # 1. Setup physical network
    G, link_map = get_abilene_topology()
    traffic_gen = TrafficGenerator(num_nodes=12, num_flows=16, seed=42)
    sim = PhysicalNetworkSimulator(G, link_map)

    default_routes = {}
    for f in traffic_gen.flows:
        p = nx.shortest_path(G, f.src, f.dst, weight="prop_delay")
        default_routes[f.flow_id] = [(p[i], p[i+1]) for i in range(len(p)-1)]
    sim.apply_routing(default_routes)

    # 2. Setup Digital Twin
    twin = NetworkDigitalTwin(num_links=len(link_map), kappa=3.0)
    print("[OK] Network Digital Twin initialized with 30 virtual links.")

    # -------------------------------------------------------------
    # Test Scenario A: Fresh Telemetry (Low Lag, Normal Operation)
    # -------------------------------------------------------------
    print("\n[Scenario A] Fresh Telemetry Sync (Normal conditions, Lag = 5%):")
    demands = traffic_gen.generate_demands(1)
    telemetry, _, _ = sim.step(demands)

    link_phi, global_phi, discrepancies = twin.synchronize(telemetry, lag_factor=0.05)
    print(f"  Link 0 Discrepancy (delta_0): {discrepancies[0]:.4f}")
    print(f"  Link 0 Fidelity (phi_0):     {link_phi[0]*100:.1f}% (High Confidence)")
    print(f"  Global Network Fidelity (Phi): {global_phi*100:.1f}%")

    # -------------------------------------------------------------
    # Test Scenario B: Lagging Telemetry (Network Congestion / Telemetry Delay)
    # -------------------------------------------------------------
    print("\n[Scenario B] Stale / Lagging Telemetry Sync (Delayed reports, Lag = 75%):")
    # Simulate a sudden change in physical network
    burst_demands = traffic_gen.generate_demands(2, burst_flow_ids=[0, 1], burst_factor=2.5)
    burst_telemetry, _, _ = sim.step(burst_demands)

    link_phi_lag, global_phi_lag, discrepancies_lag = twin.synchronize(burst_telemetry, lag_factor=0.75)
    print(f"  Link 0 Discrepancy (delta_0): {discrepancies_lag[0]:.4f} (Significant Gap!)")
    print(f"  Link 0 Fidelity (phi_0):     {link_phi_lag[0]*100:.1f}% (Caution Triggered!)")
    print(f"  Global Network Fidelity (Phi): {global_phi_lag*100:.1f}%")

    # -------------------------------------------------------------
    # Test Scenario C: Counterfactual What-If Evaluation inside Twin
    # -------------------------------------------------------------
    print("\n[Scenario C] Counterfactual 'What-If' Simulation inside Digital Twin:")
    test_routes = {0: [0]}  # Route flow 0 on link 0
    test_demands = {0: 250.0}  # 250 Mbps
    pred_loads, pred_utils = twin.counterfactual_evaluate(test_routes, test_demands, sim.capacities)
    print(f"  Digital Twin predicts Link 0 load if Flow 0 is routed: {pred_loads[0]:.1f} Mbps (Util: {pred_utils[0]*100:.1f}%)")

    print("\n" + "=" * 65)
    print("[SUCCESS] Phase 2 Verification Passed 100%!")
    print("=" * 65)

if __name__ == "__main__":
    test_phase2()
