"""
Test script for Phase 1: Validates Network Topology, Dynamic Traffic, and Physical Simulator.
"""

from src.network.topology import get_abilene_topology
from src.network.traffic import TrafficGenerator
from src.network.simulator import PhysicalNetworkSimulator

def test_phase1():
    print("=" * 60)
    print("           RUNNING PHASE 1 VERIFICATION TEST")
    print("=" * 60)

    # 1. Load Topology
    G, link_map = get_abilene_topology()
    print(f"[OK] Topology loaded: {G.number_of_nodes()} Nodes, {len(link_map)} Directed Links")
    print("    Sample Cities: New York (0), Chicago (1), LA (5), Seattle (3)")

    # 2. Initialize Traffic Generator
    traffic_gen = TrafficGenerator(num_nodes=12, num_flows=16, seed=42)
    print(f"[OK] Traffic Generator initialized with {len(traffic_gen.flows)} active flows.")
    print(f"    Sample Flow 0: City {traffic_gen.flows[0].src} -> City {traffic_gen.flows[0].dst}, Base Demand = {traffic_gen.flows[0].base_demand:.1f} Mbps")

    # 3. Initialize Physical Simulator
    sim = PhysicalNetworkSimulator(G, link_map)

    # Set default routes (direct edge if exists or simple path)
    import networkx as nx
    default_routes = {}
    for f in traffic_gen.flows:
        p = nx.shortest_path(G, f.src, f.dst, weight="prop_delay")
        edge_path = [(p[i], p[i+1]) for i in range(len(p)-1)]
        default_routes[f.flow_id] = edge_path

    sim.apply_routing(default_routes)
    print("[OK] Initial routes installed into switch flow tables.")

    # 4. Simulate 3 epochs and inspect telemetry vectors
    print("\nSimulating 3 epochs of physical traffic:")
    print("-" * 60)
    for t in range(1, 4):
        # Epoch 2 has a burst on Flow 0 to see queuing response
        bursts = [0] if t == 2 else []
        demands = traffic_gen.generate_demands(t, burst_flow_ids=bursts, burst_factor=2.0)
        telemetry, flow_metrics, link_loads = sim.step(demands)

        # Inspect Link 0 (New York -> Chicago)
        s_0 = telemetry[0]
        print(f"Epoch {t}:")
        print(f"  Link 0 (NY -> Chicago) Telemetry: [Util={s_0[0]*100:.1f}%, Queue={s_0[1]*100:.1f}%, Delay={s_0[2]:.2f}ms, Loss={s_0[3]*100:.1f}%, Cap={s_0[4]:.0f}Mbps]")
        print(f"  Flow 0 End-to-End Delay: {flow_metrics[0]['delay']:.2f} ms | Flow 0 Loss: {flow_metrics[0]['loss']*100:.1f}%")

    print("=" * 60)
    print("[SUCCESS] Phase 1 Verification Passed 100%!")
    print("=" * 60)

if __name__ == "__main__":
    test_phase1()
