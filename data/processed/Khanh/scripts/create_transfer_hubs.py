import json
import os
import math

def haversine(coord1, coord2):
    # coord = [lon, lat]
    R = 6371.0
    lon1, lat1 = map(math.radians, coord1)
    lon2, lat2 = map(math.radians, coord2)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.sin(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def create_transfer_hubs(input_dir, output_dir):
    # 1. Load normalized data
    nodes_path = os.path.join(input_dir, '02_normalized/nodes_normalized.json')
    edges_path = os.path.join(input_dir, '02_normalized/edges_normalized.json')
    
    with open(nodes_path, 'r', encoding='utf-8') as f:
        nodes = json.load(f)
    with open(edges_path, 'r', encoding='utf-8') as f:
        edges = json.load(f)

    stations = [n for n in nodes if n.get('type') == 'station']
    
    # 2. Pure Distance-based Clustering (Single Linkage)
    # Threshold 200m: a station joins a cluster if it is near ANY member.
    clusters = [] 
    DIST_THRESHOLD = 0.2 # 200 meters

    for station in stations:
        matched_cluster_indices = []
        for i, cluster in enumerate(clusters):
            # Check proximity to any existing member in this cluster
            if any(haversine(station['coords'], member['coords']) < DIST_THRESHOLD for member in cluster):
                matched_cluster_indices.append(i)
        
        if not matched_cluster_indices:
            # Create new cluster
            clusters.append([station])
        else:
            # Join the first matched cluster
            first_idx = matched_cluster_indices[0]
            clusters[first_idx].append(station)
            
            # If multiple clusters matched, merge them all into the first one
            if len(matched_cluster_indices) > 1:
                new_merged = clusters[first_idx]
                for idx in sorted(matched_cluster_indices[1:], reverse=True):
                    new_merged.extend(clusters.pop(idx))
                clusters[first_idx] = new_merged

    # 3. Virtual Hub Creation
    new_nodes = list(nodes)
    new_edges = list(edges)
    
    TRANSFER_PENALTY = 3.0  # 3km virtual penalty
    HALF_PENALTY = TRANSFER_PENALTY / 2

    hub_count = 0
    for cluster_stations in clusters:
        if len(cluster_stations) < 2:
            continue
            
        hub_id = f"hub_{hub_count}"
        hub_count += 1
        
        # Calculate mean coordinates for the hub node
        avg_lon = sum(s['coords'][0] for s in cluster_stations) / len(cluster_stations)
        avg_lat = sum(s['coords'][1] for s in cluster_stations) / len(cluster_stations)
        
        # Generate a descriptive name based on members (taking names of first 2 members)
        distinct_names = list(dict.fromkeys([s['name_ru'] for s in cluster_stations]))
        hub_name = "Hub: " + " / ".join(distinct_names[:2])
        if len(distinct_names) > 2: hub_name += "..."

        new_nodes.append({
            'id': hub_id,
            'name_ru': hub_name,
            'type': 'hub',
            'coords': [avg_lon, avg_lat]
        })
        
        # Bi-directional edges: Station <-> Hub
        for s in cluster_stations:
            new_edges.append({'source': s['id'], 'target': hub_id, 'weight': HALF_PENALTY, 'type': 'transfer'})
            new_edges.append({'source': hub_id, 'target': s['id'], 'weight': HALF_PENALTY, 'type': 'transfer'})

    # 4. Save results
    out_dir = os.path.join(output_dir, '03_connected_network')
    os.makedirs(out_dir, exist_ok=True)
    
    with open(os.path.join(out_dir, 'nodes_with_hubs.json'), 'w', encoding='utf-8') as f:
        json.dump(new_nodes, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, 'edges_with_hubs.json'), 'w', encoding='utf-8') as f:
        json.dump(new_edges, f, ensure_ascii=False, indent=2)

    print(f"Transfer Hub creation complete (V3 - Pure Distance 200m):")
    print(f"- Total Hubs created: {hub_count}")
    print(f"- Total Nodes now: {len(new_nodes)}")
    print(f"- Total Edges now: {len(new_edges)}")

if __name__ == "__main__":
    create_transfer_hubs('data/processed/Khanh/', 'data/processed/Khanh/')
