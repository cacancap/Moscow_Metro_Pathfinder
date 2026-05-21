from collections import deque


def bfs_search(adjacency_list, nodes_data, start_node, target_node, blocked_edges=None, blocked_nodes=None):
    """
    Breadth-First Search for path with minimum number of nodes.
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

    # BFS with queue: track visited nodes and parent nodes
    queue = deque([start_node])
    visited = {start_node}
    came_from = {}
    distances = {node: 0 for node in nodes_data}  # For BFS, distance = number of hops

    while queue:
        current = queue.popleft()

        if current == target_node:
            # Reconstruct path
            path = [current]
            total_distance = 0
            node = current
            while node in came_from:
                prev_node = came_from[node]
                # Calculate edge weight for total distance
                edge_info = adjacency_list.get(prev_node, {}).get(node, {})
                weight = edge_info.get('weight') if isinstance(edge_info, dict) else edge_info
                total_distance += weight if isinstance(weight, (int, float)) else 0
                path.append(prev_node)
                node = prev_node
            path.reverse()
            return path, total_distance

        neighbors = adjacency_list.get(current, {})
        for neighbor, edge_info in neighbors.items():
            if neighbor in visited:
                continue

            if neighbor in blocked_nodes:
                continue

            edge_id = edge_info.get('edge_id') if isinstance(edge_info, dict) else None
            if edge_id and edge_id in blocked_edges:
                continue

            visited.add(neighbor)
            came_from[neighbor] = current
            queue.append(neighbor)

    return None, float('infinity')
