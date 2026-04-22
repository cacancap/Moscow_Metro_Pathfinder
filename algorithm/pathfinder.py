import json
import os
import heapq

class MoscowMetroPathFinder:
    def __init__(self, adj_map_path, station_dict_path):
        """Khởi tạo hệ thống với Adjacency Map và Station Dictionary"""
        # Nạp đồ thị kề (adj_map)
        with open(adj_map_path, 'r', encoding='utf-8') as f:
            self.graph = json.load(f)
            
        # Nạp từ điển ga (station_dict) - Dạng Dictionary chuẩn
        with open(station_dict_path, 'r', encoding='utf-8') as f:
            self.station_dict = json.load(f)
        
        print(f"Hệ thống sẵn sàng: {len(self.station_dict)} ga tàu đã được nạp.")
        # print("test 5 keys: ", end='')
        # for i in range(1,5):
        #     print(self)

    def find_shortest_path(self, source_station_id, dest_station_id):
        """Tìm đường dựa trên Station ID (Trả về danh sách edge_id)"""
        # Ép kiểu ID về string để khớp với Key trong JSON
        source_id = str(source_station_id)
        dest_id = str(dest_station_id)
        print("Source: ", source_id)
        print("dest: ", dest_id)
        print("test: ", self.station_dict.get(dest_id))
        # Kiểm tra sự tồn tại của Ga trong Từ điển O(1)
        if source_id not in self.station_dict or dest_id not in self.station_dict:
            print(f"Lỗi: Không tìm thấy ID ga ({source_id} hoặc {dest_id}) trong danh sách.")
            return []

        # Lấy stop đại diện cho Ga (phần tử đầu tiên trong danh sách stops)
        start_stop = self.station_dict[source_id]['stops'][0]
        end_stop = self.station_dict[dest_id]['stops'][0]

        # Thuật toán Dijkstra tìm đường giữa các stop
        distances = {start_stop: 0}
        came_from = {} # Lưu vết: node_hien_tai: (node_truoc, edge_id)
        priority_queue = [(0, start_stop)]

        while priority_queue:
            current_dist, u = heapq.heappop(priority_queue)

            if u == end_stop:
                break

            if current_dist > distances.get(u, float('inf')):
                continue

            # Duyệt các đỉnh kề từ adj_map
            for v, edge_data in self.graph.get(u, {}).items():
                weight = edge_data['weight']
                new_dist = current_dist + weight
                
                if new_dist < distances.get(v, float('inf')):
                    distances[v] = new_dist
                    came_from[v] = (u, edge_data['edge_id'])
                    heapq.heappush(priority_queue, (new_dist, v))

        # Truy vết để lấy danh sách edge_id từ Xuất phát -> Đích
        return self._reconstruct_path(came_from, start_stop, end_stop)

    def _reconstruct_path(self, came_from, start, end):
        if end not in came_from and start != end:
            return []
            
        path = []
        curr = end
        while curr != start:
            prev_node, edge_id = came_from[curr]
            path.append(edge_id)
            curr = prev_node
            
        path.reverse() # Đảo ngược để có trình tự từ nguồn đến đích
        return path

# ==========================================
# KHỐI CHẠY KIỂM THỬ
# ==========================================
if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Điều chỉnh đường dẫn chính xác tới thư mục outputs
    output_dir = os.path.normpath(os.path.join(current_dir, '..', 'data', 'processed', 'outputs'))
    
    adj_map_path = os.path.join(output_dir, 'adjacency_list.json')
    station_dict_path = os.path.join(output_dir, 'station_dict.json') # Tên file bạn xuất từ build_dataset.py
    
    try:
        pathfinder = MoscowMetroPathFinder(adj_map_path, station_dict_path)
        
        # Thử nghiệm tìm đường giữa 2 Station ID
        start_id = "60660466" 
        dest_id = "5202107564"  
        
        result = pathfinder.find_shortest_path(start_id, dest_id)
        
        if result:
            print("\n✅ TÌM ĐƯỜNG THÀNH CÔNG!")
            print(f"Lộ trình đi qua {len(result)} cạnh.")
            print("Danh sách Edge IDs:", result)
        else:
            print(f"\n❌ Không tìm thấy đường đi giữa Ga {start_id} và Ga {dest_id}.")
            
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")