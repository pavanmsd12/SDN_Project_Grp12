# Digital-Twin-Assisted Predictive AI Routing (FiDRO-MPC)

> **Group 12 Project Guide & Blueprint**  
> *A beginner-friendly overview of what happened so far, key networking terms, and the implementation plan.*

---

## 1. What Happened Until Now? (The Journey)

### Stage 1: The Initial Team Proposal
* **The original thought:** We wanted to build an SDN (Software-Defined Network) where a software controller dynamically redirects network traffic to prevent overloaded links.
* **The mentor's feedback:** Standard dynamic routing is already well-known. We needed a fresh, cutting-edge research contribution. The suggestion was to explore **Network Digital Twins (NDTs)**.

### Stage 2: The Digital Twin Concept
* We proposed running a **Network Digital Twin** in parallel with the real network.
* Instead of waiting for a network link to get clogged (reactive), the Digital Twin uses AI to forecast upcoming traffic spikes and reroute packets before congestion happens (proactive).

### Stage 3: The Trap & Formal Problem Formulation (PDF 1: `SDN_Group_12__2026.pdf`)
* When we submitted the proposal, the professor/guide introduced a critical real-world problem: **What if the Digital Twin's predictions are wrong, or its telemetry data is delayed?**
* **The Real-Life Analogy (Google Maps):**  
  Imagine Google Maps predicts a severe traffic jam on Highway 1 in 10 minutes, so it redirects thousands of cars to a small side street. But Google Maps had lagging data—Highway 1 was actually completely clear, while the side street is now choked! Two minutes later, it redirects everyone back to Highway 1. Cars keep switching back and forth erratically.
* In high-speed networks, constantly changing paths is called **Route Oscillation (Ping-Ponging)** and it causes severe packet drops and switch overload.
* This formalized **Problem P1**: How do we safely use AI predictions while protecting the network when the Digital Twin's data is imperfect?

### Stage 4: The Breakthrough Solution (PDF 2: `SDN_Group_12_Soln.pdf`)
* To solve Problem P1, the mathematical framework **FiDRO-MPC** (*Fidelity-Calibrated Distributionally Robust Model-Predictive Routing*) was designed:
  1. **Measure Twin Accuracy (Fidelity):** Check how closely the Digital Twin matches the real network right now.
  2. **Adaptive Caution:** If the Twin is 99% accurate, trust its forecast. If the Twin has high lag or error, widen safety margins and play it safe.
  3. **Control Tail Risk:** Protect against the worst 5% traffic spikes (not just the average).
  4. **Penalize Frequent Route Switching:** Never change a flow's route unless the predicted benefit clearly outweighs the cost of switching.
  5. **Receding Horizon:** Plan 5 steps ahead, apply only the 1st step, observe reality again, and repeat.

---

## 2. In-Depth Glossary: Key Concepts Explained in Plain English

Here is an elaborate, crystal-clear breakdown of every important term in this project. Each concept includes a plain-English explanation, a real-life analogy, its role in our project, and a 1-sentence summary you can use in a viva or interview.

---

### 1. SDN (Software-Defined Networking)
* **What it means in simple English:** In traditional networking, every router is an independent device running its own software and deciding how to forward packets on its own. In an **SDN**, the "brain" (the control logic) is stripped out of individual hardware switches and centralized into one master software server called the **SDN Controller**. The switches become simple "workers" that follow the controller's instructions.
* **Real-World Analogy:** Think of an **Air Traffic Control (ATC) tower**. Individual pilots don't guess where to fly or negotiate with other planes in mid-air. The ATC tower sees the entire sky, plans all routes, and instructs every plane where and when to fly.
* **Why it matters in our project:** Because all routing decisions are centralized, our AI algorithm can run on the SDN controller, see the whole network map, and push new forwarding paths to all switches in milliseconds.
* **Viva Cheat-Answer:** *"SDN decouples the control plane (the decision-maker) from the data plane (the packet forwarder), enabling centralized, programmable network optimization."*

---

### 2. Network Digital Twin (NDT)
* **What it means in simple English:** A **Digital Twin** is a living virtual software clone of a physical system. A Network Digital Twin continuously listens to the real SDN, replicates the switches and cables in software, and tracks live traffic volume.
* **Real-World Analogy:** Think of a **high-fidelity flight simulator** connected to a real airplane in flight. Whatever the plane's sensors read, the simulator mirrors. Even better: pilots can test a risky maneuver in the simulator first to see what happens before touching the real flight controls!
* **Why it matters in our project:** The controller uses the Digital Twin as a sandbox. Before rerouting millions of user packets through Link X, it runs a simulation inside the twin to confirm Link X won't crash.
* **Viva Cheat-Answer:** *"A Network Digital Twin is a real-time virtual replica of the physical SDN that mirrors network state and enables proactive simulation and what-if routing analysis."*

---

### 3. Telemetry & Twin Discrepancy ($\delta$)
* **What it means in simple English:**
  * **Telemetry:** The periodic stream of measurement data sent from physical switches to the controller (e.g., bandwidth used, queue backlog, packet loss, transmission delay).
  * **Discrepancy ($\delta_e$):** The difference or "gap" between what the physical switch reports and what the Digital Twin thinks is happening.
* **Real-World Analogy:** Your car's dashboard thermometer says it is 30°C outside, but your phone's weather app says 22°C. The difference (8°C) is the discrepancy. If the discrepancy is large, one of them has stale or incorrect data.
* **Why it matters in our project:** Telemetry takes time to travel, and packets can be delayed. When physical measurements $s(t)$ and twin state $\tilde{s}(t)$ disagree, we calculate the normalized discrepancy $\delta_e(t)$.
* **Viva Cheat-Answer:** *"Telemetry is real-time operational metric collection from switches; twin discrepancy quantifies the numerical gap between physical observations and the virtual twin's internal state."*

---

### 4. Digital-Twin Fidelity ($\phi$ and $\Phi$)
* **What it means in simple English:** **Fidelity** is a trust score between $0$ and $1$ ($0\% \text{ to } 100\%$) indicating how accurately the virtual twin mirrors the real network right now:
  * $\phi_e(t) = 1.0$: The twin matches the physical link $e$ with 100% precision.
  * $\phi_e(t) \to 0$: The twin is out-of-sync, lagging, or receiving corrupted telemetry.
  * $\Phi(t)$: The overall network-wide fidelity score (a weighted average across all links).
* **Real-World Analogy:** Think of the **cell service / GPS bars on your smartphone**. When you have 5 full bars, you trust Google Maps turn-by-turn navigation completely. When you have 1 flickering bar in a tunnel, you know the GPS arrow might be 50 meters off, so you drive more cautiously.
* **Why it matters in our project:** This is the core novelty of our paper! Existing papers assume the Digital Twin is always 100% accurate. We are the first to say: *“Measure the twin’s fidelity first. If fidelity drops, expand your safety buffers!”*
* **Viva Cheat-Answer:** *"Fidelity is an exponential decaying trust metric $\phi_e = \exp(-\kappa \delta_e)$ that dynamically measures the virtual twin's reliability relative to physical telemetry."*

---

### 5. Proactive vs. Reactive Traffic Engineering
* **What it means in simple English:**
  * **Reactive:** Waits until a link is already congested (e.g. utilization exceeds 85%), starts dropping packets, and only *then* scrambles to reroute traffic.
  * **Proactive:** Uses AI to predict that a link will get congested in the next 3 to 5 minutes, and smoothly steers incoming traffic away *before* any queue builds up.
* **Real-World Analogy:**
  * **Reactive:** You only buy an umbrella after you are already drenched in rain.
  * **Proactive:** You check the weather forecast, see an 80% chance of rain in 2 hours, and carry an umbrella in advance.
* **Why it matters in our project:** Reactive routing always causes brief periods of high latency and packet loss. Proactive routing maintains smooth, SLA-compliant network traffic around the clock.
* **Viva Cheat-Answer:** *"Reactive TE responds after threshold breaches occur, whereas proactive TE predicts future traffic patterns to mitigate congestion before performance degradation."*

---

### 6. Route Churn & Ping-Pong Oscillation ($z_{fh}$)
* **What it means in simple English:** When an automated system switches a network flow back and forth between two paths repeatedly within a short timeframe.
* **Real-World Analogy:** An indecisive driver who aggressively switches lanes every 5 seconds because one lane moves 1 km/h faster, causing tailgating and near-accidents for everyone behind them.
* **Why it matters in our project:** Every time the SDN controller changes a route, it must send `FlowMod` commands across the control channel, update switch memory (TCAM), and reorder TCP packets. Frequent switching degrades network performance. Our formulation introduces:
  * A **reconfiguration budget** ($B^{\text{route}}$): Limits total route changes per epoch.
  * A **dwell-time constraint** ($T^{\text{dwell}}$): Once a flow is placed on a path, it must stay there for a minimum amount of time.
* **Viva Cheat-Answer:** *"Route churn is frequent rerouting of traffic flows; unchecked, it causes control-plane overhead, out-of-order packets, and ping-pong instability."*

---

### 7. Multi-Step Prediction & MPNN-GRU
* **What it means in simple English:** Predicting network conditions not just for the next single second, but for a whole sequence of future time steps $h = 1, 2, \dots, H$ (e.g., 1 min, 2 min, 3 min ahead).
  * **MPNN (Message Passing Neural Network):** Understands the network topology (how switches are interconnected).
  * **GRU (Gated Recurrent Unit):** Understands the timeline (how traffic rises and falls over time).
* **Real-World Analogy:** Predicting weather not just as "will it rain at 2:00 PM?", but giving an hourly forecast for 2:00 PM, 3:00 PM, 4:00 PM, and 5:00 PM.
* **Why it matters in our project:** A single-step prediction is too short-sighted. By looking several steps ahead, the optimizer avoids rerouting into a path that looks empty now but will be jammed in two minutes.
* **Viva Cheat-Answer:** *"MPNN-GRU combines spatial graph message passing with temporal recurrent units to forecast multi-step link loads and queue dynamics."*

---

### 8. Conformal Calibration & Ambiguity Sets
* **What it means in simple English:**
  * Neural networks are often "overconfident"—they give an exact number (e.g. "traffic will be 50 Mbps") even when they are guessing wildly.
  * **Conformal Calibration:** A mathematical technique that wraps the neural network's guess in a statistically guaranteed confidence interval (e.g., "we are 95% certain the traffic will be between 42 and 58 Mbps").
  * **Ambiguity Set ($\mathcal{P}_t$):** A mathematically defined "bubble" containing all plausible probability distributions of future traffic.
* **Real-World Analogy:** A contractor says a kitchen renovation will cost $10,000. A wise homeowner sets aside a budget range of $8,500 to $12,500 to account for unexpected surprises. That range is the calibrated ambiguity set.
* **Why it matters in our project:** We dynamically expand this bubble using twin fidelity! If the twin's accuracy drops, the bubble grows larger so the controller makes safer, more conservative routing choices.
* **Viva Cheat-Answer:** *"Conformal prediction provides distribution-free finite-sample confidence bounds, while the ambiguity set bounds all plausible probability distributions around the empirical forecast."*

---

### 9. Wasserstein Distance & Dynamic Radius ($\epsilon_t$)
* **What it means in simple English:**
  * **Wasserstein Distance (Earth Mover's Distance):** A way of measuring how different two probability curves are from each other by calculating how much "dirt" you would have to shovel to turn one distribution into the other.
  * **Ambiguity Radius ($\epsilon_t$):** The maximum allowable size of that distance:
    $$\epsilon_t = \epsilon_0 + \beta_\phi(1 - \Phi(t)) + \beta_e \bar{e}(t)$$
* **Real-World Analogy:** Think of an **adjustable safety harness**. When climbing on stable, dry rock (high fidelity $\Phi \to 1$), you keep the harness comfortably loose ($\epsilon_t \approx \epsilon_0$). When the rock is wet and slippery (low fidelity $\Phi \downarrow$), you tighten the harness and double-clip your anchors ($\epsilon_t \uparrow$).
* **Why it matters in our project:** Equation (20) couples the Digital Twin to the optimizer. When the twin disagrees with reality, $\epsilon_t$ immediately expands.
* **Viva Cheat-Answer:** *"The Wasserstein metric defines probability distribution discrepancy; our dynamic radius expands the robust uncertainty ball whenever twin fidelity degrades or rolling forecast errors rise."*

---

### 10. CVaR (Conditional Value-at-Risk) & Tail Risk
* **What it means in simple English:** Standard engineering often optimizes for the **average** case. But in networking, an average utilization of 60% is useless if a 2-second burst of 100% drops thousands of banking transactions. **CVaR at 95% ($\alpha = 0.95$)** ignores the easy 95% of normal conditions and specifically calculates the average loss in the **worst 5% disaster cases**.
* **Real-World Analogy:** When designing a bridge, civil engineers do not design it for the *average* wind speed. They design it to withstand the worst 1% hurricane gust. That is CVaR.
* **Why it matters in our project:** By minimizing CVaR in our objective function, our routing algorithm guarantees that even if an extreme traffic spike hits, packets won't be dropped.
* **Viva Cheat-Answer:** *"CVaR measures expected losses strictly in the upper $(1-\alpha)$ tail of the risk distribution, ensuring robustness against extreme congestion events."*

---

### 11. Counterfactual Digital-Twin Simulation ("What-If" Analysis)
* **What it means in simple English:** In many naive systems, people predict traffic and then find the shortest path. But that ignores an obvious fact: **changing the path alters the future traffic itself!** Counterfactual evaluation asks: *"If I choose path B instead of path A right now, what will link loads look like in 5 minutes?"*
* **Real-World Analogy:** If Google Maps notices a highway jam and directs 10,000 drivers onto a quiet village lane, that village lane will instantly become jammed. A counterfactual system models the traffic *after* the cars are moved there, not before.
* **Why it matters in our project:** The Digital Twin calculates link load as $Y_{e,h}^\omega = \sum_f \sum_p A_{ep} \hat{\lambda}_{f,h}^\omega x_{fph}$, ensuring candidate routing decisions $x$ directly shape the forecasted link utilization $\rho_{e,h}^\omega$.
* **Viva Cheat-Answer:** *"Counterfactual evaluation estimates network state conditioned on candidate routing actions $P(s_{t+h} \mid s_t, x)$, preventing routing decisions from invalidating their own forecasts."*

---

### 12. Model Predictive Control (MPC) & Receding Horizon
* **What it means in simple English:** An optimal control strategy that plans ahead for a time window (the horizon $H$, e.g., steps $1, 2, 3, 4, 5$). However, it **only applies step 1 to the real network**. Once step 1 is done, it reads new sensor data, throws away steps 2–5, and plans a fresh 5-step horizon from the new starting point.
* **Real-World Analogy:** Driving a car at night. Your headlights illuminate 100 meters ahead. You plan how to steer for that entire 100 meters, but you continuously adjust your steering wheel every second as your headlights reveal new road ahead.
* **Why it matters in our project:** Predicting 10 minutes into the future has natural error accumulation. By using a receding horizon, small prediction mistakes never compound or lock the network into a bad state.
* **Viva Cheat-Answer:** *"Receding-horizon MPC solves an open-loop multi-step optimization problem at each epoch but implements only the first control action before re-sensing and re-optimizing."*

---

### 13. Column-and-Constraint Generation (C&CG)
* **What it means in simple English:** Distributionally robust optimization has infinitely many possible traffic distributions. Solving for all of them at once would freeze any computer. **C&CG** splits the problem into two players playing a game:
  1. **Master Problem (Defender):** Picks the best route for a small set of known bad traffic scenarios.
  2. **Subproblem (Adversary):** Looks at the defender's chosen route and searches for the single worst-case traffic burst that could break it.
  3. That new worst scenario is added to the master problem, and they repeat until the adversary can no longer find any surprise that breaks the route.
* **Real-World Analogy:** A software company developing a firewall. Instead of trying to imagine every possible hack in the universe at once, they hire a "red team" hacker. Every time the hacker finds an exploit, the engineers patch that specific flaw until the hacker finds no more weaknesses.
* **Why it matters in our project:** C&CG allows our optimizer to solve complex distributionally robust problems in a few tenths of a second instead of minutes or hours.
* **Viva Cheat-Answer:** *"C&CG is an exact decomposition algorithm that iteratively alternates between a restricted master problem and an adversarial subproblem to identify worst-case uncertainty realizations."*

---

## 3. The 6 Algorithms We Will Compare

| # | Algorithm Name | How It Behaves | Why We Need It |
|---|---|---|---|
| **1** | **FiDRO-MPC** *(Our Method)* | Proactively predicts traffic, measures twin accuracy, widens safety margins if the twin is lagging, and limits route switching. | **The star of the project:** Shows best performance and zero oscillations. |
| **2** | **Reactive TE** | Has no AI, no Digital Twin. Only reroutes traffic after a link exceeds 80% capacity. | **Baseline 1:** Represents conventional, old-school networking. |
| **3** | **Deterministic MPC** | Uses AI predictions, but naively assumes the AI and Digital Twin are 100% correct all the time. | **Baseline 2:** Shows why naive prediction fails when telemetry lags. |
| **4** | **Graph-PPO** | Uses Deep Reinforcement Learning (PPO) with a Graph Neural Network to choose routes. | **Baseline 3:** Represents modern AI/RL routing methods. |
| **5** | **Standard Robust MPC** | Considers uncertainty, but uses a fixed safety margin and ignores whether the twin is accurate or lagging. | **Baseline 4:** Proves why measuring twin fidelity specifically is necessary. |
| **6** | **EXACT-MILP** | A mathematical benchmark solved to perfection by checking every single combination. | **Ground Truth:** Shows how close our algorithm is to mathematical perfection. |

---

## 4. The 12 Experimental Plots (The Final Deliverables)

1. **Maximum Link Utilization CDF:** Proves FiDRO-MPC keeps link usage safe without spikes.
2. **End-to-End Latency vs. Traffic Load:** Demonstrates lower delay as network load increases.
3. **Packet Loss / SLA Violations:** Demonstrates near-zero dropped packets during sudden bursts.
4. **Route Churn Rate:** Shows that our method eliminates ping-pong route oscillations.
5. **Twin Infidelity vs. Uncertainty Margin:** Proves the safety margin automatically widens when twin accuracy drops.
6. **Performance Under Unexpected Bursts:** Tests how each algorithm behaves when traffic spikes unexpectedly.
7. **Prediction Interval Coverage:** Shows that the AI's predicted ranges reliably contain the real future traffic.
8. **Pareto Trade-off (Delay vs. Churn):** Visualizes the balance between ultra-low delay and route stability.
9. **Optimization Convergence:** Shows that the algorithm converges within few iterations.
10. **Computation Time vs. Network Size:** Demonstrates that the algorithm makes decisions in milliseconds.
11. **Optimality Gap vs. EXACT-MILP:** Compares our runtime and quality against theoretical perfection.
12. **Ablation Study:** Compares FiDRO-MPC with and without individual components to demonstrate that each part is necessary.

---

## 5. The Step-by-Step Implementation Roadmap

```
Phase 1: Network Simulator & Telemetry Engine (Nodes, Links, Delays, Traffic Bursts)
   ↓
Phase 2: Digital Twin Engine (Synchronization, Noise Injection, Fidelity Tracking)
   ↓
Phase 3: AI Predictor (Multi-step Forecasts with Safety Bounds)
   ↓
Phase 4: Implement the 6 Routing Algorithms (FiDRO-MPC + 4 Baselines + 1 Exact)
   ↓
Phase 5: Automated Experiment Runner & Generation of All 12 Plots
   ↓
Phase 6: Project Report & Viva / Presentation Preparation Guide
```
