import json
import os
import heapq

class MoscowMetroPathFinder:
    def __init__(self, adj_map_path, stop_dict_path=None):
        """Khởi tạo hệ thống tìm đường, tải đồ thị vào bộ nhớ"""
        print(f"Đang tải đồ thị từ: {adj_map_path}...")
        with open(adj_map_path, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)
            
        # Nạp thêm từ điển trạm (nếu có) để in tên ga thay vì chỉ in ID
        self.stop_dict = {}
        if stop_dict_path and os.path.exists(stop_dict_path):
            with open(stop_dict_path, 'r', encoding='utf-8') as f:
                self.stop_dict = json.load(f)
                
        print(f"Đã tải xong hệ thống với {len(self.graph)} ga sẵn sàng phục vụ!\n")

    def get_station_name(self, node_id):
        """Hàm phụ trợ để lấy tên ga nếu có dữ liệu, nếu không trả về ID"""
        if node_id in self.stop_dict:
            return self.stop_dict[node_id].get('name', node_id)
        return str(node_id)

    def find_shortest_path(self, source_id, dest_id):
        """Thuật toán Dijkstra tìm đường đi ngắn nhất (thời gian)"""
        source_id, dest_id = str(source_id), str(dest_id)
        
        # Kiểm tra ga có tồn tại không
        if source_id not in self.graph:
            return f"Lỗi: Ga xuất phát '{source_id}' không tồn tại."
        if dest_id not in self.graph:
            return f"Lỗi: Ga đích '{dest_id}' không tồn tại."

        # Bảng lưu khoảng cách (thời gian) ngắn nhất từ start đến mọi đỉnh
        distances = {node: float('inf') for node in self.graph}
        distances[source_id] = 0
        
        # Bảng lưu Vết (Trace) để tái tạo lộ trình: node -> (node_trước_đó, dữ_liệu_cạnh)
        came_from = {node: None for node in self.graph}
        
        # Hàng đợi ưu tiên: lưu (khoảng_cách_hiện_tại, node_id)
        # Sử dụng heapq để luôn lấy ra được ga có thời gian đi ngắn nhất hiện tại
        priority_queue = [(0, source_id)]
        
        while priority_queue:
            # Lấy ra ga gần nhất
            current_dist, current_node = heapq.heappop(priority_queue)
            
            # Tối ưu: Nếu đã đến được ga đích, ta có thể dừng thuật toán sớm
            if current_node == dest_id:
                break
                
            # Bỏ qua nếu ta đã tìm thấy một đường khác ngắn hơn đến current_node từ trước
            if current_dist > distances[current_node]:
                continue
                
            # Quét tất cả láng giềng O(1)
            for neighbor_id, edge_data in self.graph[current_node].items():
                weight = edge_data['weight']
                new_dist = current_dist + weight
                
                # Nếu đường đi mới này ngắn hơn đường cũ ta từng biết
                if new_dist < distances[neighbor_id]:
                    distances[neighbor_id] = new_dist
                    came_from[neighbor_id] = (current_node, edge_data)
                    heapq.heappush(priority_queue, (new_dist, neighbor_id))

        # --- BƯỚC RECONSTRUCT LỘ TRÌNH (TRUY VẾT) ---
        if distances[dest_id] == float('inf'):
            return f"Không tìm thấy bất kỳ đường đi nào từ {source_id} đến {dest_id}."
            
        path_details = []
        current = dest_id
        
        # Đi ngược từ Đích về Xuất phát
        while current != source_id:
            prev_node, edge_used = came_from[current]
            
            # Đóng gói thông tin chặng đi
            step = {
                'from_node': prev_node,
                'from_name': self.get_station_name(prev_node),
                'to_node': current,
                'to_name': self.get_station_name(current),
                'weight_sec': edge_used['weight'],
                'line': edge_used['line_id'],
                'action': "walk" if edge_used['edge_type'] == 'transfer' else f"subway"
            }
            path_details.append(step)
            current = prev_node
            
        # Đảo ngược mảng để có lộ trình Xuất phát -> Đích
        path_details.reverse()
        
        return {
            'total_time_sec': round(distances[dest_id], 2),
            'total_time_min': round(distances[dest_id] / 60, 2),
            'path': path_details
        }

    def print_route_report(self, source_id, dest_id):
        """In báo cáo lộ trình ra màn hình console một cách đẹp mắt"""
        print(f"🔍 TÌM ĐƯỜNG: [{self.get_station_name(source_id)}] ➡️ [{self.get_station_name(dest_id)}]")
        
        result = self.find_shortest_path(source_id, dest_id)
        
        if isinstance(result, str): # Trả về chuỗi nghĩa là có lỗi/không tìm thấy
            print(result)
            return
            
        print(f"⏱️ Tổng thời gian ước tính: {result['total_time_min']} phút ({result['total_time_sec']} giây)")
        print("-" * 60)
        
        current_line = None
        for step in result['path']:
            action = step['action']
            line = step['line']
            time = round(step['weight_sec'])
            
            # Thông báo khi chuyển sang tuyến mới
            if line != current_line:
                if current_line is not None and action != "Đi bộ chuyển tuyến":
                    print(f"\n🔄 Chuyển sang Tuyến {line}:")
                current_line = line
            
            if action == "Đi bộ chuyển tuyến":
                print(f"  🚶 {action} ({time}s) tới [{step['to_name']}]")
            else:
                print(f"  🚆 {action} tới [{step['to_name']}] (Tuyến {line} - {time}s)")
                
        print("-" * 60 + "\n")

# ==========================================
# TEST THUẬT TOÁN
# ==========================================
if __name__ == "__main__":
    # Thiết lập đường dẫn đến các file dữ liệu (thay đổi tùy theo cấu trúc thư mục của bạn)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    adj_map_path = os.path.normpath(os.path.join(current_dir, '..', 'data', 'processed', 'outputs', 'adjacency_list.json'))
    stop_dict_path = os.path.normpath(os.path.join(current_dir, '..', 'data', 'processed', 'outputs', 'stop_dict_id.json'))
    
    try:
        # Khởi tạo cỗ máy tìm đường
        pathfinder = MoscowMetroPathFinder(adj_map_path, stop_dict_path)
        
        # --- NHẬP ID ĐỂ TEST ---
        # Lấy 2 ID bất kỳ có trong file json của bạn để test
        # Ví dụ giả định:
        start_station = "2101832215"  # Tự động lấy đỉnh đầu tiên
        end_station = "6938823545"   # Tự động lấy đỉnh thứ 20 (cách đó xa xa)
        
        pathfinder.print_route_report(start_station, end_station)
        
    except Exception as e:
        print(f"Lỗi khởi chạy: {e}")