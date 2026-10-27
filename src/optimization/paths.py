"""
Candidate Path Generation Module:
Generates filtered candidate path sets P_f^K for each active flow:
- K1 shortest paths by propagation delay
- K2 least-utilized paths
- K3 edge-disjoint / diverse paths
"""

import networkx as nx

class CandidatePathGenerator:
    def __init__(self, topology, k1=2, k2=1, k3=1):
        self.G = topology
        self.k1 = k1  # shortest paths
        self.k2 = k2  # least utilized
        self.k3 = k3  # disjoint paths

    def generate_candidate_paths(self, flows, current_link_utils=None, link_map=None):
        """
        Generates candidate paths for all active flows.
        Returns:
            candidate_paths: dict of flow_id -> list of paths (where path is list of edges [(u, v), ...])
        """
        candidate_paths = {}

        for flow in flows:
            src, dst = flow.src, flow.dst
            paths = []

            # 1. K1 Shortest Paths by Propagation Delay
            try:
                gen = nx.shortest_simple_paths(self.G, src, dst, weight="prop_delay")
                for _ in range(self.k1):
                    node_path = next(gen)
                    edge_path = [(node_path[i], node_path[i+1]) for i in range(len(node_path)-1)]
                    if edge_path not in paths:
                        paths.append(edge_path)
            except (nx.NetworkXNoPath, StopIteration):
                pass

            # 2. K2 Least-Utilized Paths (penalizing heavily loaded links)
            if current_link_utils is not None and link_map is not None:
                # Create a weighted graph where edge weight = prop_delay * (1 + 5 * util)
                G_util = self.G.copy()
                for (u, v), lid in link_map.items():
                    u_val = current_link_utils.get(lid, 0.0)
                    base_delay = self.G[u][v]["prop_delay"]
                    G_util[u][v]["effective_cost"] = base_delay * (1.0 + 5.0 * (u_val ** 2))

                try:
                    gen_util = nx.shortest_simple_paths(G_util, src, dst, weight="effective_cost")
                    for _ in range(self.k2):
                        node_path = next(gen_util)
                        edge_path = [(node_path[i], node_path[i+1]) for i in range(len(node_path)-1)]
                        if edge_path not in paths:
                            paths.append(edge_path)
                except (nx.NetworkXNoPath, StopIteration):
                    pass

            # 3. K3 Disjoint / Diverse Paths
            if len(paths) > 0 and self.k3 > 0:
                # Find path in graph with primary path edges temporarily penalized
                G_temp = self.G.copy()
                for edge in paths[0]:
                    if G_temp.has_edge(edge[0], edge[1]):
                        G_temp[edge[0]][edge[1]]["prop_delay"] += 1000.0  # high penalty

                try:
                    alt_path = nx.shortest_path(G_temp, src, dst, weight="prop_delay")
                    edge_path = [(alt_path[i], alt_path[i+1]) for i in range(len(alt_path)-1)]
                    if edge_path not in paths:
                        paths.append(edge_path)
                except nx.NetworkXNoPath:
                    pass

            # Fallback if no paths found
            if not paths:
                shortest = nx.shortest_path(self.G, src, dst, weight="prop_delay")
                paths.append([(shortest[i], shortest[i+1]) for i in range(len(shortest)-1)])

            candidate_paths[flow.flow_id] = paths

        return candidate_paths
