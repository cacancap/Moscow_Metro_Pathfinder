import json
import math
import os

DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "data", "processed", "Khanh", "04_final_output", "adjacency_list.json"
)


def load_graph(filepath=DATA_PATH):
    """
    Nạp adjacency_list.json và trả về (graph, nodes).

    graph : { source_id: { target_id: weight_km } }
    nodes : { node_id: [lon, lat] }
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["graph"], data["nodes"]


def filter_graph(graph, exclude_edges):
    """
    Trả về bản sao graph với các cạnh bị cấm đã loại bỏ.

    exclude_edges : set of (source_id, target_id)
                    — gom từ nhiều tuyến bị cấm trước khi truyền vào.
    """
    filtered = {}
    for src, neighbors in graph.items():
        filtered[src] = {
            tgt: w for tgt, w in neighbors.items()
            if (src, tgt) not in exclude_edges
        }
    return filtered


def haversine(nodes, node_a, node_b):
    """
    Khoảng cách chim bay (km) giữa hai node — dùng làm heuristic h(n) cho A*.
    nodes : { node_id: [lon, lat] }
    """
    lon1, lat1 = nodes[node_a]
    lon2, lat2 = nodes[node_b]

    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))