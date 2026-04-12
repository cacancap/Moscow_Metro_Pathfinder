import json
import os

def build_adjacency_map(graph_filepath):
    if not os.path.exists(graph_filepath):
        raise FileNotFoundError(f"Không tìm thấy file: {graph_filepath}")
        
    with open(graph_filepath, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)

    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])

    # Khởi tạo Từ điển kề (Adjacency Map)
    adj_map = {}

    # ==========================================
    # BƯỚC 1: TẠO TẬP KEY NGUỒN 
    # ==========================================
    for node in nodes:
        node_id = node.get('node_id')
        if node_id:
            adj_map[node_id] = {}

    # ==========================================
    # BƯỚC 2: DUYỆT EDGES VÀ XÂY DỰNG KEY ĐÍCH
    # ==========================================
    missing_nodes = set() 

    for edge in edges:
        source = edge.get('source_node')
        target = edge.get('target_node')
        
        if source in adj_map:
            # Lưu trực tiếp vào từ điển đích. 
            # Dữ liệu OSM Subway đảm bảo đơn đồ thị nên ta không cần logic check ghi đè (Multigraph)
            adj_map[source][target] = {
                'edge_id': edge.get('edge_id'),
                'weight': edge.get('weight'),
                'edge_type': edge.get('edge_type'),
                'line_id': edge.get('line_id'),
                'status': edge.get('status', 'open'),
                'geometry': edge.get('geometry', [])
            }
        else:
            missing_nodes.add(source)

    if missing_nodes:
        print(f"[CẢNH BÁO] Có {len(missing_nodes)} node_id làm source nhưng không tồn tại trong Bảng 1.")

    return adj_map

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.normpath(os.path.join(current_dir, 'clean_graph02.json'))
    output_path = os.path.normpath(os.path.join(current_dir, 'adjacency_list.json'))
    
    print(f"Đang tiến hành đọc dữ liệu từ: {input_path}")
    
    try:
        adj_map = build_adjacency_map(input_path)
        
        total_nodes = len(adj_map)
        total_connections = sum(len(targets) for targets in adj_map.values())
        isolated_nodes = sum(1 for targets in adj_map.values() if len(targets) == 0)
        isolated_nodes_list = []
        for source in adj_map.keys():
            if len(adj_map[source]) == 0:
                isolated_nodes_list.append(source)
            
        
        print("\n=== KẾT QUẢ XÂY DỰNG TỪ ĐIỂN KỀ (ADJACENCY MAP) ===")
        print(f"Tổng số Key Nguồn (Ga tàu): {total_nodes}")
        print(f"Tổng số Kết nối duy nhất: {total_connections}")
        
        if isolated_nodes > 0:
            print(f"[Lưu ý] Phát hiện {len(isolated_nodes_list)} ga bị cô lập.")
            print("Danh sách isolated_nodes: ", isolated_nodes_list)
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(adj_map, outfile, ensure_ascii=False, indent=2)
            
        print(f"\nĐã xuất Từ điển kề thành công ra file: {output_path}")
        
    except Exception as e:
        print(f"\nLỖI: {e}")