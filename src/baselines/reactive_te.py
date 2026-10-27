"""
Baseline 1: Reactive Multi-Objective Traffic Engineering
Has NO Digital Twin, NO future horizon, and NO uncertainty modeling.
Only reacts after a physical link exceeds the congestion threshold (e.g., util > 80%).
"""

class ReactiveTE_Optimizer:
    def __init__(self, topology, link_map, threshold=0.80):
        self.G = topology
        self.link_map = link_map
        self.threshold = threshold

    def solve(self, candidate_paths, current_routes, physical_telemetry):
        """
        Only triggers rerouting if a link currently in use is congested.
        """
        # Identify currently congested links from physical telemetry
        congested_links = {
            lid for lid, s_e in physical_telemetry.items()
            if s_e[0] >= self.threshold  # s_e[0] is utilization
        }

        routes = dict(current_routes)

        if not congested_links:
            # No congestion: keep existing routes (do nothing)
            return routes

        # If congested, reroute flows using those congested links
        for fid, paths in candidate_paths.items():
            curr_p = routes.get(fid, paths[0])
            curr_edges = {self.link_map[e] for e in curr_p}

            # Check if this flow traverses any congested link
            if curr_edges.intersection(congested_links):
                # Pick alternative candidate path with lowest current utilization
                best_path = curr_p
                lowest_util = 999.0
                for path in paths:
                    p_edges = [self.link_map[e] for e in path]
                    max_util_on_path = max(physical_telemetry[lid][0] for lid in p_edges)
                    if max_util_on_path < lowest_util:
                        lowest_util = max_util_on_path
                        best_path = path

                routes[fid] = best_path

        return routes
