import json
import os
from haversine import calculate_haversine_distance

# ==========================================
# CÁC HÀM PHỤ TRỢ (HELPERS)
# ==========================================
def load_way_lines(relation_filepath):
    """Ánh xạ Way ID sang Line ID từ OSM Relations"""
    way_to_line = {}
    if not os.path.exists(relation_filepath):
        return way_to_line

    with open(relation_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    elements = data.get('elements', data) if isinstance(data, dict) else data

    for el in elements:
        if el.get('type') == 'relation' and el.get('tags', {}).get('route') == 'subway':
            tags = el.get('tags', {})
            line_id = tags.get('ref', tags.get('name:en', tags.get('name', 'Unknown')))
            for member in el.get('members', []):
                if member.get('type') == 'way':
                    way_to_line[str(member.get('ref'))] = line_id
    return way_to_line

def find_nearest_station(lon, lat, stations_list, max_distance=80):
    """Tìm nhà ga gần nhất trong bán kính quy định (Snapping)"""
    nearest = None
    min_dist = max_distance
    for st in stations_list:
        dist = calculate_haversine_distance(lon, lat, st['lon'], st['lat'])
        if dist < min_dist:
            min_dist = dist
            nearest = st
    return nearest

# ==========================================
# XỬ LÝ ĐỒ THỊ CHÍNH (MAIN PIPELINE)
# ==========================================
def clean_geojson_data(filepath, relation_filepath):
    way_lines_mapping = load_way_lines(relation_filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    features = geojson_data.get('features', [])

    # === BẢNG 1: NODES (DANH SÁCH GA) ===
    nodes_table = []   

    # VÒNG 1: QUÉT GA TÀU
    for feature in features:
        if feature.get('geometry', {}).get('type') == 'Point':
            props = feature.get('properties', {})
            if props.get('station') == 'subway' or props.get('railway') == 'station':
                lon, lat = feature.get('geometry').get('coordinates')
                
                raw_id = feature.get('id', '')
                node_id = raw_id.split('/')[-1] if '/' in raw_id else raw_id

                nodes_table.append({
                    'node_id': node_id,
                    'name_en': props.get('name:en', props.get('name', '')),
                    'lat': lat,
                    'lon': lon,
                    'is_active': True
                })

    # === BẢNG 2: EDGES (CẠNH NỐI GA-GA) ===
    edges_table = []
    edge_counter = 1

    # VÒNG 2: TRƯỢT DỌC ĐƯỜNG RAY (SỬ DỤNG SNAPPING)
    for feature in features:
        if feature.get('geometry', {}).get('type') == 'LineString':
            coords = feature.get('geometry', {}).get('coordinates')
            props = feature.get('properties', {})
            
            raw_way_id = feature.get('id', '')
            osm_way_id = raw_way_id.split('/')[-1] if '/' in raw_way_id else raw_way_id
            line_id = way_lines_mapping.get(osm_way_id, props.get('ref', props.get('name', 'unknown')))

            current_start_station = None
            current_geometry = []
            current_distance = 0.0

            for i in range(len(coords)):
                lon, lat = coords[i]
                
                # Tích lũy hình học và khoảng cách
                current_geometry.append([lon, lat])
                if i > 0:
                    prev_lon, prev_lat = coords[i-1]
                    current_distance += calculate_haversine_distance(prev_lon, prev_lat, lon, lat)

                # BẮT ĐIỂM: Tìm ga trong bán kính 80m
                this_station = find_nearest_station(lon, lat, nodes_table, max_distance=80)

                if this_station is not None:
                    if current_start_station is None:
                        # Lần đầu tiên đường ray này chạm vào một nhà ga
                        current_start_station = this_station
                        current_geometry = [[lon, lat]]  # Reset để chuẩn bị vẽ đoạn tiếp theo
                        current_distance = 0.0
                    
                    elif current_start_station['node_id'] != this_station['node_id']:
                        # Đường ray đã chạm đến nhà ga tiếp theo -> Chốt cạnh!
                        weight_seconds = int(current_distance / 11.11) # Vận tốc ~40km/h

                        base_edge = {
                            'weight': weight_seconds,
                            'edge_type': 'rail',
                            'line_id': line_id,
                            'status': 'open'
                        }

                        # Chiều đi
                        edges_table.append({
                            'edge_id': f"e_{edge_counter}",
                            'source_node': current_start_station['node_id'],
                            'target_node': this_station['node_id'],
                            'geometry': current_geometry.copy(),
                            **base_edge
                        })
                        edge_counter += 1

                        # Chiều về (Ép buộc 2 chiều theo chiến lược mới)
                        edges_table.append({
                            'edge_id': f"e_{edge_counter}",
                            'source_node': this_station['node_id'],
                            'target_node': current_start_station['node_id'],
                            'geometry': list(reversed(current_geometry)), 
                            **base_edge
                        })
                        edge_counter += 1

                        # Chốt ga hiện tại làm điểm khởi hành cho chặng kế tiếp
                        current_start_station = this_station
                        current_geometry = [[lon, lat]]
                        current_distance = 0.0
                    else:
                        # Điểm này vẫn đang nằm quanh quẩn ở ga xuất phát, 
                        # bỏ qua để hình học tiếp tục được tích lũy
                        pass

    # ==========================================
    # BƯỚC 3: CLUSTERING (TRANSFER EDGES)
    # ==========================================
    WALKING_SPEED_MPS = 1.4  
    TRANSFER_PENALTY_SEC = 300 
    MAX_TRANSFER_DIST = 200 

    transfer_count = 0
    for i in range(len(nodes_table)):
        for j in range(i + 1, len(nodes_table)):
            node_A = nodes_table[i]
            node_B = nodes_table[j]
            
            dist = calculate_haversine_distance(node_A['lon'], node_A['lat'], node_B['lon'], node_B['lat'])
            
            if 0 < dist <= MAX_TRANSFER_DIST:
                weight_seconds = int((dist / WALKING_SPEED_MPS) + TRANSFER_PENALTY_SEC)
                
                transfer_base = {
                    'weight': weight_seconds,
                    'edge_type': 'transfer',
                    'line_id': 'walk',
                    'status': 'open'
                }

                edges_table.append({
                    'edge_id': f"e_{edge_counter}",
                    'source_node': node_A['node_id'],
                    'target_node': node_B['node_id'],
                    'geometry': [[node_A['lon'], node_A['lat']], [node_B['lon'], node_B['lat']]],
                    **transfer_base
                })
                edge_counter += 1
                
                edges_table.append({
                    'edge_id': f"e_{edge_counter}",
                    'source_node': node_B['node_id'],
                    'target_node': node_A['node_id'],
                    'geometry': [[node_B['lon'], node_B['lat']], [node_A['lon'], node_A['lat']]],
                    **transfer_base
                })
                edge_counter += 1
                transfer_count += 2

    return nodes_table, edges_table, transfer_count

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_path = os.path.normpath(os.path.join(current_dir, '..', 'raw', 'subway_nodes-edges.geojson'))
    relation_data_path = os.path.normpath(os.path.join(current_dir, '..', 'raw', 'subway_relations.json'))
    
    try:
        nodes_table, edges_table, transfer_count = clean_geojson_data(raw_data_path, relation_data_path)
        
        print(f"=== BẢNG 1: GA TÀU ===")
        print(f"Tổng số Ga: {len(nodes_table)}")
        
        print(f"\n=== BẢNG 2: ĐOẠN ĐƯỜNG RAY & ĐI BỘ ===")
        print(f"Tổng số Cạnh: {len(edges_table)} (Bao gồm {transfer_count} lối đi bộ chuyển tuyến)")
        
        output_path = os.path.normpath(os.path.join(current_dir, 'clean_graph.json'))
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump({'nodes': nodes_table, 'edges': edges_table}, outfile, ensure_ascii=False, indent=2)
            
        print(f"\nĐã xuất dữ liệu thành công ra file: {output_path}")
            
    except FileNotFoundError as e:
        print(f"\nLỖI: {e}")