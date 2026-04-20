from pathlib import Path
import json
import os

current_file = Path(__file__).resolve()
# thư mục chứa file (processed)
current_dir = current_file.parent
project_root = current_dir.parent.parent.parent
# đường dẫn tới file trong raw
adjacency_list_path = project_root / "data" / "processed" / "outputs" / "adjacency_list.json"

if not adjacency_list_path.exists():
    raise FileNotFoundError(f"Không tìm thấy file: {adjacency_list_path}")

try:
    with open(adjacency_list_path, 'r', encoding='utf-8') as f:
        adjacency_list = json.load(f)
        
except FileNotFoundError as e:
    print(e)



def check_graph_connectivity(adj_map):
    print("Đang phân tích tính liên thông của đồ thị...\n")
    
    # Bước 1: Thu thập TẤT CẢ các nodes (cả source và dest) để tránh sót
    all_nodes = set(adj_map.keys())
    for source, targets in adj_map.items():
        for target in targets.keys():
            all_nodes.add(target)
            
    # Bước 2: Xây dựng đồ thị vô hướng (Undirected Graph)
    # Vì tàu điện ngầm có thể đi 2 chiều, ta coi cứ có cạnh nối là có liên thông vật lý
    undirected_graph = {node: set() for node in all_nodes}
    
    for source, targets in adj_map.items():
        for target in targets.keys():
            undirected_graph[source].add(target)
            undirected_graph[target].add(source)

    # Bước 3: Dùng thuật toán BFS để tìm các cụm liên thông (Connected Components)
    visited = set()
    components = []

    for node in all_nodes:
        if node not in visited:
            # Bắt đầu phát hiện một cụm mới
            current_component = []
            queue = [node]
            visited.add(node)
            
            while queue:
                current = queue.pop(0)
                current_component.append(current)
                
                # Quét láng giềng
                for neighbor in undirected_graph[current]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            components.append(current_component)

    # Bước 4: Sắp xếp các cụm theo kích thước giảm dần (Cụm to nhất là mạng lưới chính)
    components.sort(key=len, reverse=True)

    # Bước 5: In báo cáo
    print("=== BÁO CÁO KIỂM TRA LIÊN THÔNG (CONNECTIVITY REPORT) ===")
    print(f"Tổng số Nodes hiện có: {len(all_nodes)}")
    print(f"Tổng số Cụm liên thông: {len(components)}")
    
    if len(components) == 1:
        print("✅ KẾT QUẢ: Đồ thị liên thông HOÀN TOÀN. Mọi ga đều được kết nối!")
    else:
        print("❌ KẾT QUẢ: Đồ thị BỊ ĐỨT GÃY. Mạng lưới bị chia cắt thành nhiều cụm độc lập.")
        print(f"  -> Cụm Lõi (Mạng lưới chính): Bao gồm {len(components[0])} nodes.")
        print(f"  -> Các Cụm Cô Lập (Islands): {len(components) - 1} cụm.")
        print("\n--- Chi tiết các Cụm Cô Lập ---")
        
        for i, comp in enumerate(components[1:], 1):
            if len(comp) <= 10:
                nodes_str = ", ".join(comp)
            else:
                nodes_str = ", ".join(comp[:10]) + f" ... (và {len(comp)-10} nodes khác)"
            
            print(f"  [Cụm {i}] Kích thước: {len(comp)} nodes | Các nodes: {nodes_str}")
            
    return components

if __name__ == "__main__":
    # GIẢ LẬP ĐỌC FILE (Thay đường dẫn này bằng file json thật của bạn)
    # current_dir = os.path.dirname(os.path.abspath(__file__))
    # input_path = os.path.normpath(os.path.join(current_dir, 'outputs', 'adjacency_list.json'))
    # with open(input_path, 'r', encoding='utf-8') as f:
    #     adj_map = json.load(f)
    
    # === DỮ LIỆU MẪU CỦA BẠN (DÙNG ĐỂ TEST) ===
    adj_map_sample = {
      "242546357": {
        "fake/172": {"weight": 101.2, "edge_type": "subway"},
        "296944266": {"weight": 695.1, "edge_type": "transfer"},
        "297148175": {"weight": 608.9, "edge_type": "transfer"},
        "1123660481": {"weight": 626.0, "edge_type": "transfer"},
        "5202107571": {"weight": 660.7, "edge_type": "transfer"}
      },
      "244036218": {
        "fake/67": {"weight": 1218.7, "edge_type": "subway"},
        "1191237441": {"weight": 513.7, "edge_type": "transfer"}
      },
      "252934401": {
        "fake/437": {"weight": 183.4, "edge_type": "subway"},
        "493293874": {"weight": 514.7, "edge_type": "transfer"}
      }
    }
    
    # Chạy kiểm tra
    check_graph_connectivity(adjacency_list)