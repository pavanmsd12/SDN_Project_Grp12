"""
Master Multi-Metric Comparison Dashboard:
Generates a comprehensive 4-panel visual comparison comparing all 6 algorithms
across key metrics: Mean Latency, Route Churn, Maximum Link Load, and Decision Runtime.
Saves to `plots/plot_master_comparison.png`.
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt

def generate_master_comparison():
    data_path = os.path.join("outputs", "benchmark_results.json")
    with open(data_path, "r") as f:
        results = json.load(f)

    algos = list(results.keys())

    # Key metrics calculation
    mean_delays = [np.mean(results[a]["mean_delay"]) for a in algos]
    total_churns = [sum(results[a]["route_churn"]) for a in algos]
    max_utils = [np.mean(results[a]["max_utilization"]) * 100.0 for a in algos]
    avg_runtimes = [np.mean(results[a]["runtime_ms"]) for a in algos]

    # Colors: Proposed is distinctive blue, baselines are distinct
    colors = ["#1E88E5", "#E53935", "#FB8C00", "#8E24AA", "#00897B", "#37474F"]

    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("FiDRO-MPC vs. Baselines: Master Performance Comparison", fontsize=16, fontweight="bold", y=0.98)

    # 1. Mean Latency (Lower is better)
    bars1 = axs[0, 0].bar(algos, mean_delays, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    axs[0, 0].set_title("1. End-to-End Latency (Lower is Better)", fontsize=13, fontweight="bold")
    axs[0, 0].set_ylabel("Mean Latency (ms)", fontsize=11)
    axs[0, 0].grid(axis="y", linestyle="--", alpha=0.4)
    axs[0, 0].set_xticklabels(algos, rotation=20, ha="right")
    for bar in bars1:
        h = bar.get_height()
        axs[0, 0].text(bar.get_x() + bar.get_width()/2., h + 1.2, f"{h:.1f} ms", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # 2. Total Route Churn (Lower is better)
    bars2 = axs[0, 1].bar(algos, total_churns, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    axs[0, 1].set_title("2. Total Route Churn / Ping-Ponging (Lower is Better)", fontsize=13, fontweight="bold")
    axs[0, 1].set_ylabel("Total Reconfigurations", fontsize=11)
    axs[0, 1].grid(axis="y", linestyle="--", alpha=0.4)
    axs[0, 1].set_xticklabels(algos, rotation=20, ha="right")
    for bar in bars2:
        h = bar.get_height()
        axs[0, 1].text(bar.get_x() + bar.get_width()/2., h + 1.0, f"{int(h)}", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # 3. Average Max Link Utilization (Safe headroom ~60-80%)
    bars3 = axs[1, 0].bar(algos, max_utils, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    axs[1, 0].axhline(80, color="red", linestyle="--", linewidth=1.5, label="Safe Threshold (80%)")
    axs[1, 0].set_title("3. Average Peak Link Utilization (Safe Headroom)", fontsize=13, fontweight="bold")
    axs[1, 0].set_ylabel("Peak Link Utilization (%)", fontsize=11)
    axs[1, 0].grid(axis="y", linestyle="--", alpha=0.4)
    axs[1, 0].set_xticklabels(algos, rotation=20, ha="right")
    axs[1, 0].legend(loc="upper left")
    for bar in bars3:
        h = bar.get_height()
        axs[1, 0].text(bar.get_x() + bar.get_width()/2., h + 1.2, f"{h:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # 4. Decision Runtime (Real-time capability)
    bars4 = axs[1, 1].bar(algos, avg_runtimes, color=colors, width=0.55, edgecolor="black", linewidth=0.8)
    axs[1, 1].axhline(2000, color="gray", linestyle=":", label="SDN Epoch Limit (2000 ms)")
    axs[1, 1].set_title("4. Controller Decision Time (Real-Time Speed)", fontsize=13, fontweight="bold")
    axs[1, 1].set_ylabel("Solver Latency (ms)", fontsize=11)
    axs[1, 1].grid(axis="y", linestyle="--", alpha=0.4)
    axs[1, 1].set_xticklabels(algos, rotation=20, ha="right")
    axs[1, 1].legend(loc="upper right")
    for bar in bars4:
        h = bar.get_height()
        axs[1, 1].text(bar.get_x() + bar.get_width()/2., h + 5.0, f"{h:.1f} ms", ha="center", va="bottom", fontsize=10, fontweight="bold")

    plt.tight_layout()
    out_file = os.path.join("plots", "plot_master_comparison.png")
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"[OK] Master comparison dashboard successfully saved to: {out_file}")

if __name__ == "__main__":
    generate_master_comparison()
