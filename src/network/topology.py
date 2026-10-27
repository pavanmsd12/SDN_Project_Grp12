"""
Network Topology Module: Standard SNDlib Abilene Network (12 nodes, 30 directed links).
Defines switches, directed links, bandwidth capacities, propagation delays, and coordinates.
"""

import networkx as nx

def get_abilene_topology():
    """
    Constructs the standard Abilene 12-node research topology.
    Nodes represent US metropolitan hubs:
    0: New York, 1: Chicago, 2: Washington DC, 3: Seattle, 4: Sunnyvale,
    5: Los Angeles, 6: Denver, 7: Kansas City, 8: Houston, 9: Atlanta,
    10: Indianapolis, 11: Salt Lake City
    """
    G = nx.DiGraph()

    # Node positions (for visualization) and names
    nodes = {
        0: {"name": "New York", "pos": (-74.0, 40.7)},
        1: {"name": "Chicago", "pos": (-87.6, 41.8)},
        2: {"name": "Washington DC", "pos": (-77.0, 38.9)},
        3: {"name": "Seattle", "pos": (-122.3, 47.6)},
        4: {"name": "Sunnyvale", "pos": (-122.0, 37.4)},
        5: {"name": "Los Angeles", "pos": (-118.2, 34.0)},
        6: {"name": "Denver", "pos": (-104.9, 39.7)},
        7: {"name": "Kansas City", "pos": (-94.5, 39.1)},
        8: {"name": "Houston", "pos": (-95.3, 29.7)},
        9: {"name": "Atlanta", "pos": (-84.3, 33.7)},
        10: {"name": "Indianapolis", "pos": (-86.1, 39.7)},
        11: {"name": "Salt Lake City", "pos": (-111.8, 40.7)},
    }

    for nid, attrs in nodes.items():
        G.add_node(nid, name=attrs["name"], pos=attrs["pos"])

    # Bidirectional links with realistic transmission capacities (Mbps) and propagation delays (ms)
    link_definitions = [
        (0, 1, 1000.0, 15.0),   # NY - Chicago
        (0, 2, 1000.0, 5.0),    # NY - DC
        (1, 10, 1000.0, 6.0),   # Chicago - Indianapolis
        (2, 9, 1000.0, 12.0),   # DC - Atlanta
        (3, 4, 1000.0, 18.0),   # Seattle - Sunnyvale
        (3, 11, 1000.0, 19.0),  # Seattle - Salt Lake City
        (4, 5, 1000.0, 8.0),    # Sunnyvale - LA
        (4, 6, 1000.0, 24.0),   # Sunnyvale - Denver
        (5, 8, 1000.0, 28.0),   # LA - Houston
        (6, 11, 1000.0, 10.0),  # Denver - Salt Lake City
        (6, 7, 1000.0, 12.0),   # Denver - Kansas City
        (7, 10, 1000.0, 9.0),   # Kansas City - Indianapolis
        (7, 8, 1000.0, 16.0),   # Kansas City - Houston
        (8, 9, 1000.0, 17.0),   # Houston - Atlanta
        (9, 10, 1000.0, 11.0),  # Atlanta - Indianapolis
    ]

    link_id = 0
    link_index_map = {}

    for u, v, cap, delay in link_definitions:
        # Forward link
        G.add_edge(u, v, link_id=link_id, capacity=cap, prop_delay=delay)
        link_index_map[(u, v)] = link_id
        link_id += 1

        # Reverse link
        G.add_edge(v, u, link_id=link_id, capacity=cap, prop_delay=delay)
        link_index_map[(v, u)] = link_id
        link_id += 1

    return G, link_index_map
