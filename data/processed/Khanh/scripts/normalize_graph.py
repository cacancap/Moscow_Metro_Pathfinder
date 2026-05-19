import json
import os
import math

# Bảng ánh xạ tên màu OSM sang mã HEX (Dựa trên Moscow Metro official colors)
COLOR_MAP = {
    'red': '#E42313',
    'darkgreen': '#029A47',
    'blue': '#0072BA',
    'lightblue': '#00Bfff',
    'brown': '#A35539',
    'orange': '#F07E23',
    'violet': '#943E90',
    'yellow': '#FFCD1C',
    'gray': '#ADACAC',
    'lightgreen': '#BED12C',
    'teal': '#82C0C0',
    'pink': '#F088B6'
}

def get_hex(c):
    if not c: return None
    c = c.lower()
    if c.startswith('#'): return c.upper()
    return COLOR_MAP.get(c, c).upper()

def haversine(coord1, coord2):
    R = 6371.0
    lon1, lat1 = map(math.radians, coord1)
    lon2, lat2 = map(math.radians, coord2)
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.sin(lat2) * math.sin(dlon / 2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def normalize_coords(coords):
    return [round(coords[0], 6), round(coords[1], 6)]

def normalize_graph(input_dir, output_dir):
    with open(os.path.join(input_dir, 'stations_raw.json'), 'r', encoding='utf-8') as f:
        stations = json.load(f)
    with open(os.path.join(input_dir, 'stops_raw.json'), 'r', encoding='utf-8') as f:
        stops = json.load(f)
    with open(os.path.join(input_dir, 'tracks_raw.json'), 'r', encoding='utf-8') as f:
        tracks = json.load(f)

    node_registry = {}
    def get_node_id(coords):
        n_coords = tuple(normalize_coords(coords))
        if n_coords not in node_registry:
            node_registry[n_coords] = f"node_auto_{len(node_registry)}"
        return node_registry[n_coords], n_coords

    processed_stations = []
    processed_edges = []

    # 2. Map Stations to Stops (Matching by Name + Colour)
    for stop in stops:
        name = stop['name_ru']
        stop_colour = get_hex(stop.get('colour'))
        stop_node_id, st_coords = get_node_id(stop['coords'])
        
        # Tìm station phù hợp nhất
        candidates = [s for s in stations if s['name_ru'] == name]
        matching_station = None
        
        if len(candidates) == 1:
            matching_station = candidates[0]
        elif len(candidates) > 1:
            # Ưu tiên khớp theo màu sắc trước
            color_matches = [s for s in candidates if get_hex(s.get('colour')) == stop_colour]
            if color_matches:
                matching_station = color_matches[0]
            else:
                # Nếu không khớp màu, dùng khoảng cách gần nhất làm dự phòng cuối cùng
                min_dist = float('inf')
                for cand in candidates:
                    d = haversine(stop['coords'], cand['coords'])
                    if d < min_dist:
                        min_dist = d
                        matching_station = cand

        if matching_station:
            station_node_id, s_coords = get_node_id(matching_station['coords'])
            if not any(ps['id'] == station_node_id for ps in processed_stations):
                processed_stations.append({
                    'id': station_node_id, 
                    'name_ru': name, 
                    'name_en': matching_station['name_en'], 
                    'type': 'station',
                    'coords': s_coords, 
                    'colour': get_hex(matching_station.get('colour'))
                })

            processed_edges.append({'source': station_node_id, 'target': stop_node_id, 'weight': 0.001, 'type': 'platform'})
            processed_edges.append({'source': stop_node_id, 'target': station_node_id, 'weight': 0.001, 'type': 'platform'})

    # 3. Create Track Edges
    for track in tracks:
        coords_list = track['coords']
        oneway = track['oneway'] == 'yes'
        for i in range(len(coords_list) - 1):
            u_id, u_coords = get_node_id(coords_list[i])
            v_id, v_coords = get_node_id(coords_list[i+1])
            dist = haversine(u_coords, v_coords)
            processed_edges.append({'source': u_id, 'target': v_id, 'weight': dist, 'type': 'track', 'line': track['name_ru'], 'colour': track['colour']})
            if not oneway:
                processed_edges.append({'source': v_id, 'target': u_id, 'weight': dist, 'type': 'track', 'line': track['name_ru'], 'colour': track['colour']})

    # 4. Save
    final_nodes = []
    for coords, node_id in node_registry.items():
        node_info = {'id': node_id, 'coords': list(coords), 'type': 'way_point'}
        for s in processed_stations:
            if s['id'] == node_id:
                node_info.update(s)
                node_info['type'] = 'station'
                break
        final_nodes.append(node_info)

    out_dir = 'data/processed/Khanh/02_normalized'
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'nodes_normalized.json'), 'w', encoding='utf-8') as f: json.dump(final_nodes, f, ensure_ascii=False, indent=2)
    with open(os.path.join(out_dir, 'edges_normalized.json'), 'w', encoding='utf-8') as f: json.dump(processed_edges, f, ensure_ascii=False, indent=2)
    print(f"Normalization complete (V3 - Name + Color Matching)")

if __name__ == "__main__":
    normalize_graph('data/processed/Khanh/01_raw_extracted/', 'data/processed/Khanh/02_normalized/')
