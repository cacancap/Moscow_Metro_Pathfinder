import json
import os

class SubwayGraph:
    """
    Lớp quản lý Đồ thị Tàu điện ngầm (Adjacency Map).
    Cung cấp các phương thức truy xuất nhanh O(1) cho Team Thuật toán.
    """
    def __init__(self, filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"LỖI: Không tìm thấy file đồ thị tại {filepath}")
            
        print(f"[GraphLoader] Đang nạp đồ thị từ: {filepath}...")
        with open(filepath, 'r', encoding='utf-8') as f:
            self.adj_map = json.load(f)
            
        self.total_nodes = len(self.adj_map)
        print(f"[GraphLoader] Nạp thành công! Sẵn sàng duyệt {self.total_nodes} nhà ga.")

    def get_all_nodes(self):
        """Trả về danh sách ID của tất cả các nhà ga."""
        return list(self.adj_map.keys())

    def get_neighbors(self, node_id):
        """
        Lấy danh sách các ga lân cận có thể đi tới từ node_id.
        Trả về: Dictionary { 'target_id': { edge_data } }
        """
        return self.adj_map.get(str(node_id), {})

    def get_edge_data(self, source_id, target_id):
        """
        Lấy toàn bộ thông tin của cạnh nối giữa 2 ga (weight, line_id, edge_type...).
        """
        source_id, target_id = str(source_id), str(target_id)
        if source_id in self.adj_map and target_id in self.adj_map[source_id]:
            return self.adj_map[source_id][target_id]
        return None

    def get_weight(self, source_id, target_id):
        """
        Truy xuất siêu tốc Trọng số (thời gian di chuyển) giữa 2 ga.
        Trả về None nếu không có đường nối trực tiếp.
        """
        edge_data = self.get_edge_data(source_id, target_id)
        if edge_data:
            return edge_data.get('weight')
        return None

# ==========================================
# HƯỚNG DẪN SỬ DỤNG CHO TEAM THUẬT TOÁN
# ==========================================
if __name__ == "__main__":
    # 1. Khởi tạo đường dẫn (Giả sử file chạy cùng thư mục với json)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    graph_path = os.path.normpath(os.path.join(current_dir, '..', 'data', 'processed', 'outputs', 'adjacency_list.json'))
    
    try:
        # 2. Nạp đồ thị vào bộ nhớ (Chỉ làm 1 lần lúc start server)
        metro_graph = SubwayGraph(graph_path)
        
        # --- DEMO CÁC TÍNH NĂNG ---
        print("\n--- DEMO CHO THUẬT TOÁN DIJKSTRA ---")
        
        # Lấy thử 1 node ngẫu nhiên có kết nối để test
        test_source = next((k for k, v in metro_graph.adj_map.items() if len(v) > 0), None)
        
        if test_source:
            # 3. Lấy các đỉnh kề (Hành động lặp nhiều nhất trong BFS/Dijkstra)
            neighbors = metro_graph.get_neighbors(test_source)
            print(f"Từ ga [{test_source}], có thể đi tới {len(neighbors)} ga khác:")
            
            for target_node, edge_info in neighbors.items():
                weight = edge_info['weight']
                line = edge_info['line_id']
                action = "Đi tàu" if edge_info['edge_type'] == 'rail' else "Đi bộ chuyển tuyến"
                
                print(f"  -> Ga [{target_node}] | Mất {weight} giây | {action} (Tuyến: {line})")
                
            # 4. Truy xuất trực tiếp O(1)
            test_target = list(neighbors.keys())[0]
            fast_weight = metro_graph.get_weight(test_source, test_target)
            print(f"\n[Test O(1)] Thời gian từ {test_source} đến {test_target} là: {fast_weight}s")

    except FileNotFoundError as e:
        print(e)