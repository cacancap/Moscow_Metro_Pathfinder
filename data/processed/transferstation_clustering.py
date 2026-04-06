import json
import math
from haversine import calculate_haversine_distance

def cluster_transfer_stations(graph_data, max_transfer_distance=200):
    vertices = graph_data['vertices']
    edges = graph_data['edges']
    
    # BƯỚC 1: Lọc ra danh sách chỉ chứa các Ga (không lấy Shape Points)
    stations = {node_id: data for node_id, data in vertices.items() 
                if data.get('station') == 'subway' and data.get('name')}
    
    station_ids = list(stations.keys())
    transfer_edges_added = 0

    # BƯỚC 2: Duyệt mọi cặp nhà ga để tìm khoảng cách gần
    for i in range(len(station_ids)):
        for j in range(i + 1, len(station_ids)):
            id_A = station_ids[i]
            id_B = station_ids[j]
            
            # Bỏ qua nếu cùng một tên và cùng một tuyến (tránh tự nối chính nó)
            if stations[id_A].get('colour') == stations[id_B].get('colour'):
                continue
                
            dist = calculate_haversine_distance(
                stations[id_A]['lon'], stations[id_A]['lat'],
                stations[id_B]['lon'], stations[id_B]['lat']
            )
            
            # BƯỚC 3: Nếu khoảng cách < ngưỡng, tạo cạnh chuyển tuyến
            if dist <= max_transfer_distance:
                # Phạt trọng số: 1 lần chuyển tuyến tương đương việc phải đi thêm 600 mét
                penalty_distance = dist + 600 
                
                transfer_attr = {
                    'name': 'Lối đi bộ chuyển tuyến',
                    'transfer': 'yes',
                    'mode': 'walk',
                    'distance_m': round(penalty_distance, 2),
                    'real_distance': round(dist, 2) # Giữ lại khoảng cách thật để hiển thị UI
                }
                
                # Nối A -> B
                edges.append({'source': id_A, 'target': id_B, 'attributes': transfer_attr})
                # Nối B -> A
                edges.append({'source': id_B, 'target': id_A, 'attributes': transfer_attr})
                
                transfer_edges_added += 2

    return {'vertices': vertices, 'edges': edges}, transfer_edges_added