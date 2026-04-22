import heapq
import time
from collections import deque

from .graph import haversine


# ── Helpers ────────────────────────────────────────────────────────────────────

def _reconstruct_path(came_from, start, goal):
    path = []
    node = goal
    while node != start:
        path.append(node)
        node = came_from[node]
    path.append(start)
    path.reverse()
    return path


def _path_distance(graph, path):
    return sum(graph[path[i]][path[i + 1]] for i in range(len(path) - 1))


# ── Algorithms ─────────────────────────────────────────────────────────────────

def _bfs(graph, nodes, start, goal):
    """Tìm đường ít ga nhất (không quan tâm trọng số)."""
    queue = deque([start])
    came_from = {start: None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbor in graph.get(current, {}):
            if neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)

    if goal not in came_from:
        return None
    return _reconstruct_path(came_from, start, goal)


def _dijkstra(graph, nodes, start, goal):
    """Tìm đường ngắn nhất theo km."""
    dist = {start: 0.0}
    came_from = {}
    heap = [(0.0, start)]
    visited = set()

    while heap:
        g, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            break
        for neighbor, weight in graph.get(current, {}).items():
            new_g = g + weight
            if new_g < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_g
                came_from[neighbor] = current
                heapq.heappush(heap, (new_g, neighbor))

    if goal not in came_from and goal != start:
        return None
    return _reconstruct_path(came_from, start, goal)


def _astar(graph, nodes, start, goal):
    """Tìm đường ngắn nhất bằng A* (Dijkstra + Haversine heuristic)."""
    h0 = haversine(nodes, start, goal)
    dist = {start: 0.0}
    came_from = {}
    heap = [(h0, 0.0, start)]   # (f, g, node)
    visited = set()

    while heap:
        f, g, current = heapq.heappop(heap)
        if current in visited:
            continue
        visited.add(current)
        if current == goal:
            break
        for neighbor, weight in graph.get(current, {}).items():
            new_g = g + weight
            if new_g < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_g
                came_from[neighbor] = current
                h = haversine(nodes, neighbor, goal)
                heapq.heappush(heap, (new_g + h, new_g, neighbor))

    if goal not in came_from and goal != start:
        return None
    return _reconstruct_path(came_from, start, goal)


# ── Public API ─────────────────────────────────────────────────────────────────

_ALGOS = {"bfs": _bfs, "dijkstra": _dijkstra, "astar": _astar}


def find_path(graph, nodes, start_id, goal_id, algorithm="astar"):
    """
    Tìm đường từ start_id đến goal_id.

    Parameters
    ----------
    graph     : { source_id: { target_id: weight_km } }
    nodes     : { node_id: [lon, lat] }
    algorithm : "bfs" | "dijkstra" | "astar"

    Returns
    -------
    {
        "path"        : [node_id, ...],
        "distance_km" : float,
        "num_stations": int,
        "elapsed_ms"  : float,
    }
    hoặc None nếu không tìm được đường.
    """
    if algorithm not in _ALGOS:
        raise ValueError(f"Thuật toán không hợp lệ: '{algorithm}'. Chọn: {list(_ALGOS)}")

    if start_id == goal_id:
        return {"path": [start_id], "distance_km": 0.0, "num_stations": 1, "elapsed_ms": 0.0}

    t0 = time.perf_counter()
    path = _ALGOS[algorithm](graph, nodes, start_id, goal_id)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 3)

    if path is None:
        return None

    return {
        "path": path,
        "distance_km": round(_path_distance(graph, path), 4),
        "num_stations": len(path),
        "elapsed_ms": elapsed_ms,
    }