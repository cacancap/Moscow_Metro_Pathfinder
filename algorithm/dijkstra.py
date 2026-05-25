import heapq


def dijkstra_search(adjacency_list, nodes_data, start_node, target_node, blocked_edges=None, blocked_nodes=None):
    """
    Dijkstra's algorithm for shortest path finding.
    Returns (path, total_distance) or (None, infinity) if no path exists.
    """
    if start_node not in nodes_data or target_node not in nodes_data:
        return None, float('infinity')

    if blocked_edges is None:
        blocked_edges = set()
    else:
        blocked_edges = set(blocked_edges)

    if blocked_nodes is None:
        blocked_nodes = set()
    else:
        blocked_nodes = set(blocked_nodes)

    if start_node in blocked_nodes or target_node in blocked_nodes:
        return None, float('infinity')

    # Priority queue: (distance, node)
    open_set = [(0, start_node)]
    distances = {node: float('infinity') for node in nodes_data}
    distances[start_node] = 0
    came_from = {}
    visited = set()

    while open_set:
        current_distance, current = heapq.heappop(open_set)

        if current in visited:
            continue

        visited.add(current)

        if current == target_node:
            # Reconstruct path
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path, distances[target_node]

        neighbors = adjacency_list.get(current, {})
        for neighbor, edge_info in neighbors.items():
            if neighbor in blocked_nodes:
                continue

            edge_id = edge_info.get('edge_id') if isinstance(edge_info, dict) else None
            if edge_id and edge_id in blocked_edges:
                continue

            weight = edge_info.get('weight') if isinstance(edge_info, dict) else edge_info
            new_distance = distances[current] + weight

            if new_distance < distances[neighbor]:
                distances[neighbor] = new_distance
                came_from[neighbor] = current
                heapq.heappush(open_set, (new_distance, neighbor))

    return None, float('infinity')
