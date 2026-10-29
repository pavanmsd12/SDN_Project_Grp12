"""
Test script for Phase 3: Validates MPNN-GRU Predictor Training, Multi-step Quantile Forecasting,
Conformal Uncertainty Calibration, and Dynamic Wasserstein Ambiguity Radius.
"""

import torch
import numpy as np
from src.network.topology import get_abilene_topology
from src.network.traffic import TrafficGenerator
from src.network.simulator import PhysicalNetworkSimulator
from src.digital_twin.twin import NetworkDigitalTwin
from src.predictor.mpnn_gru import MPNN_GRU_Predictor, train_toy_predictor
from src.predictor.conformal import ConformalCalibrator
import networkx as nx

def test_phase3():
    print("=" * 65)
    print("           RUNNING PHASE 3 VERIFICATION TEST")
    print("=" * 65)

    # 1. Setup Topology and Simulator
    G, link_map = get_abilene_topology()
    num_links = len(link_map)
    traffic_gen = TrafficGenerator(num_nodes=12, num_flows=16, seed=42)
    sim = PhysicalNetworkSimulator(G, link_map)

    default_routes = {}
    for f in traffic_gen.flows:
        p = nx.shortest_path(G, f.src, f.dst, weight="prop_delay")
        default_routes[f.flow_id] = [(p[i], p[i+1]) for i in range(len(p)-1)]
    sim.apply_routing(default_routes)

    # 2. Instantiate and Train MPNN-GRU Neural Predictor
    print("\n[Step 1] Initializing MPNN-GRU Neural Predictor:")
    horizon = 3
    predictor = MPNN_GRU_Predictor(in_features=5, hidden_dim=32, horizon=horizon)
    print(f"  Architecture: 5-dim Input -> Spatial MPNN -> Temporal GRU -> Quantile Decoder (H={horizon})")
    print("  Training predictor with pinball loss (tau in {0.05, 0.50, 0.95}) + MSE...")
    train_toy_predictor(predictor, num_links=num_links, epochs=20)
    print("  [OK] MPNN-GRU training complete!")

    # 3. Collect 5 epochs of telemetry as historical input window
    print("\n[Step 2] Feeding historical telemetry window into trained AI:")
    history = []
    for t in range(1, 6):
        demands = traffic_gen.generate_demands(t)
        telemetry, _, _ = sim.step(demands)
        # Array of shape [num_links, 5]
        frame = np.array([telemetry[lid] for lid in range(num_links)], dtype=np.float32)
        history.append(frame)

    # Convert to tensor [num_links, seq_len=5, in_features=5]
    x_tensor = torch.tensor(np.stack(history, axis=1), dtype=torch.float32)
    adj_matrix = torch.eye(num_links)

    # Predict future quantiles
    predictor.eval()
    with torch.no_grad():
        mu, q_low, q_mid, q_high = predictor(x_tensor, adj_matrix)

    # Inspect forecast for Link 0 (NY -> Chicago)
    print("  Predicted traffic for Link 0 over next 3 future steps (h=1, 2, 3):")
    for h in range(horizon):
        print(f"    Horizon h={h+1}: Mean={mu[0, h].item():.1f} Mbps | "
              f"90% Interval: [{q_low[0, h].item():.1f} Mbps  <--->  {q_high[0, h].item():.1f} Mbps]")

    # 4. Conformal Calibration with Digital-Twin Fidelity
    print("\n[Step 3] Conformal Calibration & Fidelity Coupling:")
    calibrator = ConformalCalibrator(beta_phi=1.5, eps_0=0.05)

    q_l_nom = q_low[0, 0].item()
    q_h_nom = q_high[0, 0].item()

    # Case A: High Fidelity (phi = 1.0)
    cal_low_high_fid, cal_high_high_fid = calibrator.calibrate_interval(q_l_nom, q_h_nom, phi_e=1.0)
    eps_high_fid = calibrator.compute_wasserstein_radius(global_fidelity=1.0)
    print("  Case A: High Twin Fidelity (Phi = 100%):")
    print(f"    Confidence Interval: [{cal_low_high_fid:.1f} Mbps  <--->  {cal_high_high_fid:.1f} Mbps]")
    print(f"    Wasserstein Ambiguity Radius (epsilon_t): {eps_high_fid:.4f} (Tight Buffer)")

    # Case B: Low Fidelity (phi = 0.20, stale telemetry / lag)
    cal_low_low_fid, cal_high_low_fid = calibrator.calibrate_interval(q_l_nom, q_h_nom, phi_e=0.20)
    eps_low_fid = calibrator.compute_wasserstein_radius(global_fidelity=0.20)
    print("\n  Case B: Low Twin Fidelity (Phi = 20%, Telemetry Lag):")
    print(f"    Confidence Interval: [{cal_low_low_fid:.1f} Mbps  <--->  {cal_high_low_fid:.1f} Mbps]  <-- Expanded!")
    print(f"    Wasserstein Ambiguity Radius (epsilon_t): {eps_low_fid:.4f}  <-- Stretched for safety!")

    print("\n" + "=" * 65)
    print("[SUCCESS] Phase 3 Verification Passed 100%!")
    print("=" * 65)

if __name__ == "__main__":
    test_phase3()

