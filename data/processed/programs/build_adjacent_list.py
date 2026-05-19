from pathlib import Path
import json
import os

current_file = Path(__file__).resolve()
# thư mục chứa file (processed)
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent
# đường dẫn tới file graph

edge_list_path = project_root / "data" / "processed" / "outputs" / "edge_list.json"
stop_dict_id_path = project_root / "data" / "processed" / "outputs" / "stop_dict_id.json"
stop_dict_coord_path = project_root / "data" / "processed" / "outputs" / "stop_dict_coord.json"

if not (edge_list_path.exists() or stop_dict_id_path.exists()):
    raise FileNotFoundError(f"Không tìm thấy file")

try:
    with open(edge_list_path, 'r', encoding='utf-8') as f:
        edge_list = json.load(f)
        
    with open(stop_dict_id_path, 'r', encoding='utf-8') as f:
        stop_dict_id = json.load(f)
        
    with open(stop_dict_coord_path, 'r', encoding='utf-8') as f:
        stop_dict_coord = json.load(f)
        
except FileNotFoundError as e:
    print(e)


def build_adjacency_map():
    
    nodes = (list(stop_dict_coord.values()))
    edges = edge_list

    # Khởi tạo Từ điển kề (Adjacency Map)
    adj_map = {}

    # ==========================================
    # BƯỚC 1: TẠO TẬP KEY NGUỒN 
    # ==========================================
    for node in nodes:
        node_id = node.get('id')
        if node_id:
            adj_map[node_id] = {}

    # ==========================================
    # BƯỚC 2: DUYỆT EDGES VÀ XÂY DỰNG KEY ĐÍCH
    # ==========================================
    missing_nodes = set() 

    for edge in edges:
        source = edge.get('source_id')
        dest = edge.get('dest_id')
        
        if source in adj_map:
            # Lưu trực tiếp vào từ điển đích. 
            # Dữ liệu OSM Subway đảm bảo đơn đồ thị nên ta không cần logic check ghi đè (Multigraph)
            adj_map[source][dest] = {
                'edge_id': edge.get('edge_id'),
                'weight': edge.get('weight'),
                'edge_type': edge.get('edge_type'),
                'line_id': edge.get('line_id'),
                'colour': edge.get('colour'),
                'geometry': edge.get('geometry', [])
            }
        else:
            missing_nodes.add(source)

    if missing_nodes:
        print(f"[CẢNH BÁO] Có {len(missing_nodes)} node_id làm source nhưng không tồn tại trong Bảng 1.")

    return adj_map

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # FIX: đọc và ghi vào thư mục outputs/ thay vì cạnh file
    output_path = os.path.normpath(os.path.join(current_dir, '..', 'outputs', 'adjacency_list.json'))
    
    
    try:
        adj_map = build_adjacency_map()
        adj_keys = list(adj_map.keys())
        isolated_source = []
        for key1, value1 in adj_map.items():
            if (value1 is None):
                isolated_source.append(key1)
            for key2 in value1.keys():
                if (key2 in adj_keys): adj_keys.remove(key2)
                
        isolated_count = 0
        print("Isolated nodes: ", end='')
        for key in adj_keys:
            if key in isolated_source:
                print(key)
                count += 1
        print("Total isolated: ", isolated_count)
        print("total isolated source: ", len(isolated_source))
        print("total isolated dest: ", len(adj_keys))
                
        
        # total_nodes = len(adj_map)
        # total_connections = sum(len(targets) for targets in adj_map.values())
        # isolated_nodes = sum(1 for targets in adj_map.values() if len(targets) == 0)
        # isolated_nodes_list = []
        # for source in adj_map.keys():
        #     if len(adj_map[source]) == 0:
        #         isolated_nodes_list.append(source)
            
        
        # print("\n=== KẾT QUẢ XÂY DỰNG TỪ ĐIỂN KỀ (ADJACENCY MAP) ===")
        # print(f"Tổng số Key Nguồn (Ga tàu): {total_nodes}")
        # print(f"Tổng số Kết nối duy nhất: {total_connections}")
        
        # if isolated_nodes > 0:
        #     print(f"[Lưu ý] Phát hiện {len(isolated_nodes_list)} ga bị cô lập.")
        #     print("Danh sách isolated_nodes: ", isolated_nodes_list)
        with open(output_path, 'w', encoding='utf-8') as outfile:
            json.dump(adj_map, outfile, ensure_ascii=False, indent=2)
            
        print(f"\nĐã xuất Từ điển kề thành công ra file: {output_path}")
        
    except Exception as e:
        print(f"\nLỖI: {e}")