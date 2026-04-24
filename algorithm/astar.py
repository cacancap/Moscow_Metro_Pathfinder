import heapq
from .heuristics import calculate_haversine_distance


def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


# 1. THÊM THAM SỐ: blocked_nodes=None
def a_star_search(adjacency_list, nodes_data, start_node, target_node, blocked_edges=None, blocked_nodes=None):
    if start_node not in nodes_data or target_node not in nodes_data:
        return None, float('infinity')

    # Khởi tạo set để lookup nhanh O(1)
    if blocked_edges is None:
        blocked_edges = set()
    else:
        blocked_edges = set(blocked_edges)

    # 2. KHỞI TẠO SET CHO CÁC GA BỊ ĐÓNG CỬA
    if blocked_nodes is None:
        blocked_nodes = set()
    else:
        blocked_nodes = set(blocked_nodes)

    # 3. KIỂM TRA NGAY TỪ ĐẦU: Nếu điểm đi hoặc điểm đến đang bị đóng cửa thì báo lỗi luôn
    if start_node in blocked_nodes or target_node in blocked_nodes:
        return None, float('infinity')

    target_coords = nodes_data[target_node]
    t_lon, t_lat = target_coords.get('lon'), target_coords.get('lat')

    open_set = []
    heapq.heappush(open_set, (0, start_node))

    came_from = {}
    g_score = {node: float('infinity') for node in nodes_data}
    g_score[start_node] = 0
    f_score = {node: float('infinity') for node in nodes_data}

    start_coords = nodes_data[start_node]
    s_lon, s_lat = start_coords.get('lon'), start_coords.get('lat')
    f_score[start_node] = calculate_haversine_distance(s_lon, s_lat, t_lon, t_lat)

    while open_set:
        current_f, current = heapq.heappop(open_set)

        if current == target_node:
            return reconstruct_path(came_from, current), g_score[current]

        if current_f > f_score[current]:
            continue

        neighbors = adjacency_list.get(current, {})
        for neighbor, edge_info in neighbors.items():

            # --- 4. LOGIC CHẶN GA (NODES) ---
            # Nếu ga láng giềng nằm trong danh sách đóng cửa -> BỎ QUA KHÔNG ĐI VÀO GA ĐÓ
            if neighbor in blocked_nodes:
                continue
            # -------------------------------

            # --- LOGIC CHẶN ĐƯỜNG (EDGES) ĐÃ LÀM TRƯỚC ĐÓ ---
            edge_id = edge_info.get('edge_id') if isinstance(edge_info, dict) else None
            if edge_id and edge_id in blocked_edges:
                continue
            # -----------------------------------------------

            weight = edge_info.get('weight') if isinstance(edge_info, dict) else edge_info
            tentative_g_score = g_score[current] + weight

            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score

                neighbor_coords = nodes_data[neighbor]
                n_lon, n_lat = neighbor_coords.get('lon'), neighbor_coords.get('lat')

                h = calculate_haversine_distance(n_lon, n_lat, t_lon, t_lat)
                f_score[neighbor] = tentative_g_score + h

                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None, float('infinity')