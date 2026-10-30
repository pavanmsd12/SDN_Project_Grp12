# FiDRO-MPC: Viva & Presentation Defense Guide
> **Group 12 Final Project Cheat-Sheet**  
> *Everything you need to explain, present, and defend this project with confidence.*

---

## 1. The 60-Second "Elevator Pitch" (Memorize This!)

> *"In Software-Defined Networks (SDN), traditional routing is **reactive**—it only reroutes traffic after congestion has already occurred and packets are being dropped.*
> 
> *To fix this, we created **FiDRO-MPC**, a proactive traffic engineering framework that uses a **Network Digital Twin (NDT)** and an **AI Predictor (MPNN-GRU)** to forecast traffic spikes and reroute traffic ahead of time.*
> 
> *Our core research novelty solves a critical real-world problem: **What if the Digital Twin has stale, lagging telemetry?** Instead of blindly trusting predictions, FiDRO-MPC measures the twin's **Fidelity score ($\Phi$)**. When fidelity drops, our controller automatically expands its safety margins using **Wasserstein distributionally robust optimization** and suppresses **route oscillation (ping-ponging)**.*
> 
> *We evaluated FiDRO-MPC against **5 competing algorithms** across **12 performance plots**, proving that our method achieves zero packet loss during sudden bursts and completely eliminates ping-pong route churn."*

---

## 2. Top 10 Viva Questions & Winning Answers

### Q1: What is the main novelty of your project?
* **Your Answer:**  
  *"Most existing papers assume that a Network Digital Twin is 100% synchronized with the physical network at all times. In reality, telemetry has delays, sensor noise, and network lag. Our core novelty is **Fidelity Calibration (Eq. 20)**: we explicitly measure twin discrepancy $\delta_e$, calculate a fidelity score $\phi_e$, and dynamically scale our uncertainty bounds and risk sensitivity so the controller plays it safe when the twin is lagging."*

### Q2: Why did you use SDN instead of traditional routing?
* **Your Answer:**  
  *"In traditional routing (like OSPF or BGP), routers make decentralized, short-sighted decisions based only on immediate neighbors. SDN centralizes the control plane into a software controller that has a global, network-wide view, allowing our AI to dynamically push optimal multi-hop paths to all switches simultaneously."*

### Q3: What is the difference between a Packet and a Flow? Does your controller route every packet?
* **Your Answer:**  
  *"No, routing every packet at the controller would cause control-plane overload and crash the network. The controller programs flow tables for **entire traffic flows** (streams of packets with matching source, destination, and ports). The switches forward millions of packets in hardware at line rate, while the controller only updates rules when traffic conditions shift."*

### Q4: What are the 5 numbers in your Telemetry Vector $s_e(t)$?
* **Your Answer:**  
  *"For every link, physical switches report:  
  1. $u_e$: Link Utilization (% bandwidth used)  
  2. $q_e$: Queue Occupancy (% buffer filled)  
  3. $d_e$: Delay (latency in ms)  
  4. $\ell_e$: Packet Loss Rate  
  5. $C_e$: Maximum Link Capacity (1000 Mbps)"*

### Q5: How does your AI predictor work? Why MPNN-GRU?
* **Your Answer:**  
  *"We use an **MPNN-GRU** architecture:  
  - The **MPNN (Message Passing Neural Network)** learns the **spatial topology** (how switches are interconnected across the map).  
  - The **GRU (Gated Recurrent Unit)** captures the **temporal trend** (how traffic rises and falls over time).  
  Instead of predicting a single risky point number, it outputs **pinball quantiles ($q_{0.05}, \mu, q_{0.95}$)** wrapped in **conformal prediction bounds** to provide guaranteed confidence intervals."*

### Q6: What is CVaR and why did you use it instead of average cost?
* **Your Answer:**  
  *"CVaR stands for **Conditional Value-at-Risk**. Standard engineering minimizes average delay, but in networking, an average of 50% utilization is useless if a 2-second burst of 100% drops thousands of critical packets. **CVaR at 95%** specifically optimizes and protects against the **worst 5% disaster tail events**."*

### Q7: What is Route Churn or Ping-Pong Oscillation, and how do you prevent it?
* **Your Answer:**  
  *"Route churn is when an indecisive controller switches a flow back and forth between two paths rapidly. Every switch change requires control-plane messages (`FlowMod`), consumes switch memory (TCAM), and reorders packets. We prevent this using:  
  1. A **reconfiguration budget** ($B^{\text{route}}$) that limits total changes per epoch.  
  2. A **dwell-time constraint** ($T^{\text{dwell}}$) that forces a flow to stay on a path for a minimum duration.  
  3. A **switching penalty** ($\lambda_C$) in the objective function."*

### Q8: What is Receding Horizon Control (MPC)?
* **Your Answer:**  
  *"Model Predictive Control looks $H=3$ steps into the future, plans the best path sequence, but **installs only the first action $x_1^*$** into the physical switches. At the next epoch, it collects fresh telemetry, re-synchronizes the twin, and plans again. This prevents long-range forecasting errors from accumulating."*

### Q9: Name the 6 algorithms you compared.
* **Your Answer:**  
  1. **FiDRO-MPC (Our Method):** Fidelity-aware robust predictive routing.  
  2. **Reactive-TE (Baseline 1):** Traditional threshold-based TE (no twin, no prediction).  
  3. **Deterministic-MPC (Baseline 2):** Point prediction without uncertainty or fidelity awareness.  
  4. **Graph-PPO (Baseline 3):** Deep Reinforcement Learning (PPO + GNN).  
  5. **Uncalibrated-DR (Baseline 4):** Robust MPC with static uncertainty, ignoring twin fidelity.  
  6. **EXACT-MILP (Benchmark):** Branch-and-bound integer linear program giving the theoretical upper bound.

### Q10: What did the benchmark results prove?
* **Your Answer:**  
  *"Reactive-TE experienced high link over-utilization (85.9%) and caused 86 panicked route changes. Graph-PPO was unstable with 34 route changes. Deterministic-MPC caused 35 route changes due to prediction errors. **Our FiDRO-MPC achieved safe utilization (60.8%), low latency (55.5 ms), and exactly ZERO unnecessary route churn.**"*

---

## 3. How to Present the 12 Plots (Quick Reference)

| Plot File | What to Point to on Screen | What to Say to the Professor |
| :--- | :--- | :--- |
| **`plot01_utilization_cdf.png`** | Look at the vertical dashed line at 80%. | *"Notice how our blue curve stays safely to the left of 80%, while Reactive-TE crosses the red danger zone."* |
| **`plot02_latency_vs_load.png`** | Look at the load scale going from 0.8x to 2.0x. | *"As network load doubles, our latency grows gently, while Reactive-TE blows up exponentially due to queuing congestion."* |
| **`plot03_packet_loss_bursts.png`** | Look at the shaded orange and red burst zones. | *"When sudden bursts hit at epochs 7 and 14, FiDRO-MPC achieves 0% packet loss because it proactively steered traffic away ahead of time."* |
| **`plot04_route_churn.png`** | Look at the flat blue line at 0 vs. the climbing red line. | *"Reactive-TE caused 86 route reconfigurations, causing massive switch overhead. Our method kept routes completely stable."* |
| **`plot05_fidelity_coupling.png`** | Notice the curve sloping downward from left to right. | *"This validates Equation (20): when twin fidelity drops, our uncertainty radius $\epsilon_t$ automatically expands to protect the network."* |
| **`plot06_ood_burst_robustness.png`** | Look at the red horizontal line at 1.0 (capacity limit). | *"Even under extreme 3.0x unexpected bursts, FiDRO-MPC prevents links from exceeding 100% capacity."* |
| **`plot07_conformal_coverage.png`** | Notice the blue line above the 90% target. | *"Our conformal calibration guarantees that real traffic falls within our predicted bounds >95% of the time."* |
| **`plot08_pareto_delay_churn.png`** | Look at the tradeoff curve. | *"Demonstrates the Pareto trade-off: we can tune the parameter $\lambda_C$ to achieve the perfect balance between low latency and route stability."* |
| **`plot09_ccg_convergence.png`** | Notice the upper and lower bounds meeting at step 3. | *"Proves our Column-and-Constraint Generation solver converges rapidly in just 3 iterations."* |
| **`plot10_runtime_scalability.png`** | Look at the ~260 ms bar for FiDRO-MPC. | *"Shows that our decision takes only 260 milliseconds, well within standard SDN epoch intervals of 2 to 5 seconds."* |
| **`plot11_optimality_gap.png`** | Look at the small horizontal bar. | *"FiDRO-MPC is within 3% of the theoretical mathematical optimum (EXACT-MILP) while running 100x faster on large graphs."* |
| **`plot12_ablation_study.png`** | Look at the height of the bars without each feature. | *"Removing fidelity coupling ($\beta_\phi=0$) increases latency and churn, proving that every component of our paper is necessary."* |

---

## 4. Project Structure (Where Everything Lives)

```
SDN_Project_Grp12/
├── README.md                  # Comprehensive beginner-friendly documentation & glossary
├── VIVA_GUIDE.md              # Project presentation & viva defense cheat-sheet
├── run_simulation.py          # Master execution script (benchmark + plots)
├── generate_all_plots.py      # Plotting engine generating all 12 publication figures
├── test_phase1.py             # Phase 1 verification test (Topology & Simulator)
├── test_phase2.py             # Phase 2 verification test (Digital Twin & Fidelity)
├── test_phase3.py             # Phase 3 verification test (AI Predictor & Conformal)
├── test_phase4.py             # Phase 4 verification test (All 6 Algorithms)
├── outputs/                   # Raw benchmark JSON data (20 epochs)
├── plots/                     # All 12 generated publication-quality PNG figures
└── src/
    ├── network/               # Topology, traffic generator, physical simulator
    ├── digital_twin/          # Network Digital Twin, discrepancy, fidelity scoring
    ├── predictor/             # MPNN-GRU neural network, pinball loss, conformal calibrator
    ├── optimization/          # Candidate path generator, FiDRO-MPC optimizer, EXACT-MILP
    ├── baselines/             # Reactive-TE, Deterministic-MPC, Graph-PPO, Uncalibrated-DR
    └── evaluation/            # Receding-horizon benchmark orchestrator
```
