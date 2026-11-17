# Fidelity-Calibrated Distributionally Robust Model-Predictive Routing in SDN (FiDRO-MPC)

**Course Project — Group 12**  
*Department of Computer Science & Engineering*

---

## Abstract

Software-Defined Networking (SDN) centralizes control logic, enabling programmable global traffic engineering. However, conventional SDN routing schemes are largely **reactive**, recomputing paths only after congestion thresholds are breached, leading to buffer overflow and packet loss. While recent approaches deploy **Network Digital Twins (NDTs)** to predict traffic proactively, they overlook a critical operational challenge: **telemetry synchronization latency and measurement errors between the physical network and the virtual twin.** A naive controller that optimizes against a single forecast under desynchronized twin telemetry triggers catastrophic **route oscillations (ping-ponging)**.

This project implements **FiDRO-MPC** (*Fidelity-Calibrated Distributionally Robust Model-Predictive Routing*), an end-to-end framework that explicitly couples Digital-Twin fidelity assessment with distributionally robust optimization. FiDRO-MPC continuously evaluates a link- and network-level fidelity score $\Phi(t) \in (0, 1]$. When twin fidelity degrades, the controller dynamically inflates the radius $\epsilon_t$ of a Wasserstein ambiguity set, switching to a conservative routing policy that controls tail congestion via **Conditional Value-at-Risk (CVaR)** while enforcing route-reconfiguration budgets and dwell-time constraints.

---

## System Architecture

```
+-----------------------------------------------------------------------------------+
|                            SDN CONTROL PLANE (FiDRO-MPC)                          |
|                                                                                   |
|  +--------------------+      +--------------------+      +---------------------+  |
|  | Physical Telemetry | ---> | Network Digital    | ---> | Dynamic Fidelity    |  |
|  | Collection s(t)    |      | Twin Sync s_tilde  |      | Assessment Phi(t)   |  |
|  +--------------------+      +--------------------+      +---------------------+  |
|                                                                     |             |
|                                                                     v             |
|  +--------------------+      +--------------------+      +---------------------+  |
|  | Receding-Horizon   | <--- | C&CG Robust Master | <--- | Wasserstein Ball    |  |
|  | Execution (x_1*)   |      | Solver (CVaR_0.95) |      | Calibration (eps_t) |  |
|  +--------------------+      +--------------------+      +---------------------+  |
+-----------------------------------------------------------------------------------+
                                      | FlowMod Rules
                                      v
+-----------------------------------------------------------------------------------+
|               PHYSICAL DATA PLANE (12-Node SNDlib Abilene Backbone)               |
|      12 Switch Nodes | 30 Directed Links | M/M/1 Queuing Dynamics | Telemetry s_e |
+-----------------------------------------------------------------------------------+
```

### Core Components

1. **Physical Network Simulation (`src/network/`):**
   * Implements the standard 12-node, 30-link Abilene national backbone topology with standardized 1 Gbps transmission capacities and geographic speed-of-light propagation delays.
   * Models dynamic traffic demands incorporating 24-epoch diurnal sinusoidal waves, Gaussian variance, and injected burst spikes.
   * Simulates $M/M/1$-inspired queuing dynamics, buffer bloat, and packet drop probabilities under line-rate forwarding.
   * Periodically outputs a 5-dimensional telemetry vector per link: $s_e(t) = [u_e(t), q_e(t), d_e(t), \ell_e(t), C_e(t)]$.

2. **Network Digital Twin & Fidelity Tracking (`src/digital_twin/`):**
   * Maintains the virtual network state $\tilde{s}_e(t)$ synchronized via physical telemetry.
   * Computes normalized twin discrepancy:
     $$\delta_e(t) = \sum_{k=1}^K \omega_k \frac{|s_{e,k}(t) - \tilde{s}_{e,k}(t)|}{R_k + \epsilon}$$
   * Computes link-level fidelity $\phi_e(t) = \exp(-\kappa \delta_e(t))$ and traffic-weighted global fidelity $\Phi(t) = \sum_{e} \nu_e(t) \phi_e(t)$.
   * Enables counterfactual "what-if" evaluation of candidate routing matrices conditioned on predicted exogenous demands.

3. **Topology-Aware Prediction & Conformal Calibration (`src/predictor/`):**
   * Employs an **MPNN-GRU** (Message Passing Neural Network + Gated Recurrent Unit) architecture for multi-step spatial-temporal traffic forecasting over horizon $H=3$.
   * Trained via pinball loss to output point estimates along with quantile bounds ($\tau \in \{0.05, 0.50, 0.95\}$).
   * Couples twin fidelity to the Wasserstein ambiguity radius (Equation 20):
     $$\epsilon_t = \epsilon_0 + \beta_\phi(1 - \Phi(t)) + \beta_e \bar{e}(t)$$

4. **Distributionally Robust Receding-Horizon Optimizer (`src/optimization/`):**
   * Formulates the multi-objective traffic engineering problem combining expected latency, peak link utilization, route reconfiguration overhead, and worst-case tail risk:
     $$\min_{x, z, \eta} \sum_{h=1}^H \gamma^{h-1} \left[ J_h^{\text{nom}} + \lambda_R \sup_{Q \in \mathcal{P}_t} \text{CVaR}_\alpha^Q(V_h) \right] + \lambda_C \sum_{h=1}^H \sum_f c_f^R z_{fh}$$
   * Enforces flow conservation, candidate path assignment, link capacity limits, reconfiguration budgets ($\sum_f z_{fh} \le B^{\text{route}}$), and route dwell-time constraints ($T^{\text{dwell}}$).
   * Solved using Column-and-Constraint Generation (C&CG) with linear programming relaxation and branch-and-bound.

---

## Algorithms Compared

The framework evaluates 6 routing algorithms under identical multi-epoch traffic conditions:

1. **FiDRO-MPC (Proposed):** Fidelity-calibrated distributionally robust model-predictive routing with dynamic Wasserstein ambiguity sets and CVaR tail risk.
2. **Reactive-TE (Baseline 1):** Traditional threshold-based traffic engineering ($u_e \ge 80\%$) with zero foresight and no digital twin.
3. **Deterministic-MPC (Baseline 2):** Point-predictive NDT routing optimizing strictly against the mean forecast with no uncertainty modeling.
4. **Graph-PPO (Baseline 3):** Deep Reinforcement Learning routing using a graph state encoder and Proximal Policy Optimization actor-critic.
5. **Uncalibrated-DR (Baseline 4):** Distributionally robust MPC with a static uncertainty set radius, ignoring twin fidelity variations.
6. **EXACT-MILP (Benchmark):** Deterministic equivalent mixed-integer linear program solved to global mathematical optimality.

---

## Experimental Benchmark Results

Evaluated across a 20-epoch dynamic evaluation timeline on the Abilene topology with periodic traffic bursts and telemetry lag injections:

| Algorithm | Avg Link Load | Mean Latency | Packet Loss Rate | Route Churn | Decision Time |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **FiDRO-MPC (Proposed)** | **60.8%** | **55.52 ms** | **0.0%** | **0** | **262.6 ms** |
| **Reactive-TE** | 85.9% | 80.69 ms | 8.2% | 86 | 0.2 ms |
| **Deterministic-MPC** | 57.8% | 56.69 ms | 4.1% | 35 | 265.3 ms |
| **Graph-PPO** | 70.7% | 74.98 ms | 5.3% | 34 | 15.2 ms |
| **Uncalibrated-DR** | 61.2% | 56.27 ms | 0.0% | 0 | 214.6 ms |
| **EXACT-MILP** | 57.4% | 57.04 ms | 0.0% | 50 | 149.1 ms |

### Key Findings
* **Elimination of Route Oscillation:** While Reactive-TE triggered 86 route reconfigurations and Deterministic-MPC caused 35 flips due to prediction error, FiDRO-MPC achieved **0 route churn**.
* **Zero Packet Loss under Sudden Bursts:** Proactive quantile forecasting and CVaR headroom preserved 0% packet loss during sudden 2.4x traffic surges.
* **Real-Time Feasibility:** FiDRO-MPC decision latency averaged 262.6 ms, well within standard SDN control intervals (2 to 5 seconds).

---

## Repository Structure

```
.
├── src/
│   ├── network/               # Physical SDN topology, dynamic traffic, and queuing simulator
│   │   ├── topology.py        # SNDlib Abilene 12-node network graph
│   │   ├── traffic.py         # Dynamic diurnal & burst traffic generator
│   │   └── simulator.py       # Physical data plane & telemetry collector
│   ├── digital_twin/          # Network Digital Twin & telemetry synchronization
│   │   └── twin.py            # Discrepancy metric and fidelity scoring module
│   ├── predictor/             # Spatial-temporal forecasting & uncertainty bounds
│   │   ├── mpnn_gru.py        # MPNN-GRU neural network architecture
│   │   └── conformal.py       # Conformal calibration & Wasserstein radius module
│   ├── optimization/          # Robust routing optimization algorithms
│   │   ├── paths.py           # Candidate path generation (delay, load, disjoint)
│   │   ├── fidro_mpc.py       # Proposed FiDRO-MPC solver
│   │   └── exact_milp.py      # EXACT-MILP global benchmark solver
│   ├── baselines/             # Comparative baseline algorithms
│   │   ├── reactive_te.py     # Threshold-triggered reactive TE
│   │   ├── deterministic_mpc.py # Mean-prediction point NDT MPC
│   │   ├── graph_ppo.py       # GNN-PPO reinforcement learning router
│   │   └── uncalibrated_dr.py # Fixed-radius uncalibrated robust MPC
│   └── evaluation/            # Multi-epoch simulation harness
│       └── benchmark.py       # Receding-horizon benchmark orchestrator
├── plots/                     # 12 publication-quality comparison figures + master dashboard
├── outputs/                   # Raw multi-epoch benchmark telemetry and metrics (JSON)
├── run_simulation.py          # Master benchmark execution pipeline
├── generate_all_plots.py      # Automated generator for Plots 1 through 12
├── generate_master_dashboard.py # 4-panel master performance dashboard generator
├── test_phase1.py             # Phase 1 verification: Network & Telemetry
├── test_phase2.py             # Phase 2 verification: Digital Twin & Fidelity
├── test_phase3.py             # Phase 3 verification: AI Predictor & Conformal Bounds
├── test_phase4.py             # Phase 4 verification: Multi-Algorithm Stress Test
└── README.md                  # Project documentation
```

---

## Execution Instructions

### Prerequisites
* Python 3.10+
* Required libraries: `torch`, `networkx`, `numpy`, `scipy`, `matplotlib`, `pulp`

Install dependencies:
```bash
pip install torch networkx numpy scipy matplotlib "pulp<3.0"
```

### 1. Run Live Multi-Algorithm Stress Test
To evaluate all 6 algorithms side-by-side on an identical traffic burst and telemetry lag epoch:
```bash
python test_phase4.py
```

### 2. Run Full 20-Epoch Benchmark & Generate All Plots
To execute the complete receding-horizon simulation across all algorithms and re-render all plots:
```bash
python run_simulation.py
```

### 3. Generate Master Comparison Dashboard
To re-render the 4-panel master comparison figure:
```bash
python generate_master_dashboard.py
```

---

## Summary of Generated Plots (`plots/`)

1. **`plot01_utilization_cdf.png`:** Cumulative distribution function of maximum link utilization.
2. **`plot02_latency_vs_load.png`:** End-to-end latency scaling under traffic load multipliers (0.8x to 2.0x).
3. **`plot03_packet_loss_bursts.png`:** Packet loss rate during sudden traffic bursts.
4. **`plot04_route_churn.png`:** Cumulative route reconfigurations demonstrating suppression of ping-ponging.
5. **`plot05_fidelity_coupling.png`:** Validation of Equation (20) coupling fidelity $\Phi(t)$ to ambiguity radius $\epsilon_t$.
6. **`plot06_ood_burst_robustness.png`:** Peak link loads under out-of-distribution traffic surges up to 3.0x.
7. **`plot07_conformal_coverage.png`:** Empirical prediction interval coverage across horizon steps $h \in \{1, 2, 3, 4\}$.
8. **`plot08_pareto_delay_churn.png`:** Pareto frontier between latency minimization and route stability.
9. **`plot09_ccg_convergence.png`:** Master-adversary bounds convergence in Column-and-Constraint Generation.
10. **`plot10_runtime_scalability.png`:** Average decision latency per control epoch across algorithms.
11. **`plot11_optimality_gap.png`:** Sub-optimality gap relative to EXACT-MILP branch-and-bound.
12. **`plot12_ablation_study.png`:** Component ablation analyzing the individual contributions of fidelity, CVaR, and churn penalties.
13. **`plot_master_comparison.png`:** 4-panel master dashboard summarizing Latency, Churn, Utilization, and Runtime.
