import json
import os
from haversine import calculate_haversine_distance
from transferstation_clustering import cluster_transfer_stations

test_nodeId = 6937381514

def clean_geojson_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    vertices = {}  
    edges = []     
    features = geojson_data.get('features', [])

    # QUÉT 1 VÒNG DUY NHẤT: Xử lý cả Ga tàu và Tuyến đường
    for feature in features:
        geom_type = feature.get('geometry', {}).get('type')
        coords = feature.get('geometry', {}).get('coordinates')
        props = feature.get('properties', {})
        feature_id = feature.get('id', '') 

        # --- XỬ LÝ ĐỈNH (GA TÀU) ---
        if geom_type == 'Point':
            lon, lat = coords
            node_id = f"{lon},{lat}" 
            
            # Ghi đè hoặc tạo mới đỉnh với đầy đủ thông tin ga
            vertices[node_id] = {
                'osm_id': feature_id,
                'lon': lon,
                'lat': lat,
                'name': props.get('name', ''),
                'name_en': props.get('name:en', ''),
                'colour': props.get('colour', ''),
                'railway': props.get('railway', ''), 
                'station': props.get('station', '')  
            }

        # --- XỬ LÝ CẠNH (ĐƯỜNG RAY) ---
        elif geom_type == 'LineString':
            cleaned_tags = {
                'name': props.get('name', 'Unknown subway'),
                'colour': props.get('colour', ''),
                'railway': props.get('railway', ''),
                'oneway': props.get('oneway', 'no'),
                'operator': props.get('operator', '')
            }

            for i in range(len(coords) - 1):
                u_lon, u_lat = coords[i]
                v_lon, v_lat = coords[i+1]
                
                u_id = f"{u_lon},{u_lat}"
                v_id = f"{v_lon},{v_lat}"

                # Nếu tọa độ đường ray chưa được quét thấy (không phải ga tàu), 
                # tạo đỉnh tạm để giữ liên kết mảng
                if u_id not in vertices:
                    vertices[u_id] = {'lon': u_lon, 'lat': u_lat, 'name': 'Shape Point', 'station': 'no'}
                
                if v_id not in vertices:
                    vertices[v_id] = {'lon': v_lon, 'lat': v_lat, 'name': 'Shape Point', 'station': 'no'}

                # Tính khoảng cách thực tế
                distance = calculate_haversine_distance(u_lon, u_lat, v_lon, v_lat)
                edge_attributes = cleaned_tags.copy()
                edge_attributes['distance_m'] = round(distance, 2)

                # 1. Nối chiều đi (u -> v)
                edges.append({'source': u_id, 'target': v_id, 'attributes': edge_attributes})

                # 2. Nối chiều về (v -> u) nếu không phải đường 1 chiều
                if cleaned_tags.get('oneway') != 'yes':
                    edges.append({'source': v_id, 'target': u_id, 'attributes': edge_attributes})

            
    return vertices, edges



if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # FIX: từ programs/ lên 2 cấp (processed/ -> data/) rồi vào raw/
    raw_data_path = os.path.normpath(os.path.join(current_dir, '..', '..', 'raw', 'subway_nodes-edges.geojson'))
    
    print(f"Đang đọc dữ liệu từ: {raw_data_path}")
    
    try:
        # 1. Trích xuất đỉnh và cạnh thô
        nodes_dict, edges_list = clean_geojson_data(raw_data_path)
        
        # 2. Nối các tuyến giao nhau
        graph_data = {'vertices': nodes_dict, 'edges': edges_list}
        final_graph, transfer_count = cluster_transfer_stations(graph_data, max_transfer_distance=200)

        # 3. In kết quả dựa trên ĐỒ THỊ ĐÃ HOÀN THIỆN (final_graph)
        print("\n=== KẾT QUẢ XỬ LÝ DỮ LIỆU MOSCOW METRO ===")
        print(f"Tổng số Đỉnh (Ga tàu + Điểm nối): {len(final_graph['vertices'])}")
        print(f"Tổng số Cạnh (Đoạn đường ray + Lối đi bộ): {len(final_graph['edges'])}")
        print(f"Số lượng Cạnh chuyển tuyến (Đi bộ) được thêm vào: {transfer_count}")

        # 4. FIX: Lưu vào thư mục outputs/ thay vì cạnh file
        output_path = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'clean_graph.json'))
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(final_graph, outfile, ensure_ascii=False, indent=2)
            
        print(f"\nĐã lưu bộ dữ liệu Graph hoàn chỉnh tại: {output_path}")
            
    except FileNotFoundError:
        print(f"\nLỖI: Không tìm thấy file. Vui lòng kiểm tra lại file tại {raw_data_path}")
    
    # FIX: Biến test_nodes không tồn tại, đã comment lại
    # print("Số lượng nodes ga nằm trên đường: ", len(test_nodes))