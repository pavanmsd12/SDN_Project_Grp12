"""
Main Master Execution Script:
Runs the complete multi-algorithm SDN simulation, logs all metrics,
and renders all 12 publication-quality plots.

Usage:
    python run_simulation.py
"""

import sys
import os
import json
import numpy as np

# Ensure root directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.evaluation.benchmark import run_comprehensive_benchmark
from generate_all_plots import generate_all_12_plots

def main():
    print("=" * 70)
    print("   FiDRO-MPC: Digital-Twin-Assisted SDN Routing Framework")
    print("   Group 12 Final Evaluation Pipeline (6 Algorithms, 12 Plots)")
    print("=" * 70)

    # 1. Run Benchmark
    benchmark_file = os.path.join("outputs", "benchmark_results.json")
    results = run_comprehensive_benchmark(total_epochs=20, output_path=benchmark_file)

    # 2. Render all 12 Plots
    generate_all_12_plots(data_path=benchmark_file, out_dir="plots")

    # 3. Print Executive Summary Table
    print("\n" + "=" * 70)
    print(f"{'ALGORITHM':<20} | {'AVG UTIL':<10} | {'DELAY (ms)':<12} | {'CHURN':<8} | {'RUNTIME (ms)':<12}")
    print("-" * 70)

    for algo, data in results.items():
        avg_u = f"{np.mean(data['max_utilization']) * 100:.1f}%"
        avg_d = f"{np.mean(data['mean_delay']):.2f}"
        total_churn = str(sum(data['route_churn']))
        avg_rt = f"{np.mean(data['runtime_ms']):.1f}"
        print(f"{algo:<20} | {avg_u:<10} | {avg_d:<12} | {total_churn:<8} | {avg_rt:<12}")

    print("=" * 70)
    print("\nExecution complete! Check the `plots/` folder for all 12 generated figures.")

if __name__ == "__main__":
    main()
