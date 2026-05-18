import json
import os
import time
from collections import deque
import heapq

def verify_graph(input_dir):
    print(f"Loading packaged data from {input_dir}...")
    with open(os.path.join(input_dir, '04_final_output/adjacency_list.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(os.path.join(input_dir, '04_final_output/station_metadata.json'), 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    graph = data['graph']
    stations = [node_id for node_id, meta in metadata.items() if meta['type'] == 'station']
    
    if not stations:
        print("Error: No stations found in metadata!")
        return

    print(f"Total stations to check: {len(stations)}")

    # 1. Connectivity Check (BFS)
    def check_connectivity(start_node):
        visited = {start_node}
        queue = deque([start_node])
        while queue:
            u = queue.popleft()
            for v in graph.get(u, {}):
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
        return visited

    start_st = stations[0]
    reachable_nodes = check_connectivity(start_st)
    
    reachable_stations = [st for st in stations if st in reachable_nodes]
    print(f"Connectivity Result: {len(reachable_stations)} / {len(stations)} stations are reachable from each other.")

    # 2. Performance Benchmark (Dijkstra)
    def dijkstra(start_node, target_node):
        distances = {node: float('infinity') for node in graph}
        distances[start_node] = 0
        pq = [(0, start_node)]
        
        while pq:
            current_dist, u = heapq.heappop(pq)
            if u == target_node: return current_dist
            if current_dist > distances[u]: continue
            
            for v, weight in graph.get(u, {}).items():
                distance = current_dist + weight
                if distance < distances[v]:
                    distances[v] = distance
                    heapq.heappush(pq, (distance, v))
        return float('infinity')

    print("Running Benchmark (100 random path searches)...")
    import random
    start_time = time.time()
    for _ in range(100):
        s1 = random.choice(stations)
        s2 = random.choice(stations)
        dijkstra(s1, s2)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 100
    print(f"Average pathfinding time: {avg_time:.4f} seconds")

    # 3. Report
    report = {
        "total_stations": len(stations),
        "reachable_stations": len(reachable_stations),
        "connectivity_pct": (len(reachable_stations) / len(stations)) * 100,
        "avg_search_time_sec": avg_time,
        "status": "PASS" if len(reachable_stations) == len(stations) and avg_time < 0.1 else "WARNING"
    }

    with open(os.path.join(input_dir, 'reports/validation_results.txt'), 'w', encoding='utf-8') as f:
        f.write(json.dumps(report, indent=2))
    
    print(f"Validation Report saved to {input_dir}/reports/validation_results.txt")

if __name__ == "__main__":
    verify_graph('data/processed/Khanh/')
