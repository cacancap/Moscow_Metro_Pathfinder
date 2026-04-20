import json
import os
import sys
from pathlib import Path

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

# Tăng giới hạn đệ quy trong Python để tránh lỗi với đồ thị lớn (nhiều ga)
sys.setrecursionlimit(10000)

def check_directed_connectivity(adj_map):
    print("Đang phân tích tính Liên Thông Mạnh (Strongly Connected) của đồ thị...\n")
    
    # Bước 1: Thu thập toàn bộ Nodes
    all_nodes = set(adj_map.keys())
    for source, targets in adj_map.items():
        for target in targets.keys():
            all_nodes.add(target)
            
    # Bước 2: Xây dựng Đồ thị gốc và Đồ thị đảo ngược chiều (Transposed Graph)
    graph = {node: [] for node in all_nodes}
    rev_graph = {node: [] for node in all_nodes}
    
    for source, targets in adj_map.items():
        for target in targets.keys():
            graph[source].append(target)
            # Đảo ngược chiều mũi tên cho đồ thị rev_graph
            rev_graph[target].append(source)

    # ==========================================
    # THUẬT TOÁN KOSARAJU - BƯỚC 1: 
    # Duyệt DFS trên đồ thị gốc để lấy thứ tự hoàn thành (Stack)
    # ==========================================
    visited = set()
    stack = []

    def dfs_pass1(node):
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs_pass1(neighbor)
        # Khi không đi tiếp được nữa thì đẩy vào stack
        stack.append(node)

    for node in all_nodes:
        if node not in visited:
            dfs_pass1(node)

    # ==========================================
    # THUẬT TOÁN KOSARAJU - BƯỚC 2: 
    # Duyệt DFS trên đồ thị đảo ngược dựa theo thứ tự Stack
    # ==========================================
    visited.clear()
    sccs = [] # Chứa các Cụm liên thông mạnh

    def dfs_pass2(node, current_scc):
        visited.add(node)
        current_scc.append(node)
        for neighbor in rev_graph[node]:
            if neighbor not in visited:
                dfs_pass2(neighbor, current_scc)

    # Rút dần từ đỉnh stack (node hoàn thành muộn nhất ở Bước 1)
    while stack:
        node = stack.pop()
        if node not in visited:
            current_scc = []
            dfs_pass2(node, current_scc)
            sccs.append(current_scc)

    # Bước 3: Sắp xếp các cụm theo kích thước để dễ quan sát
    sccs.sort(key=len, reverse=True)

    # Bước 4: In Báo cáo
    print("=== BÁO CÁO KIỂM TRA LIÊN THÔNG MẠNH (DIRECTED CONNECTIVITY) ===")
    print(f"Tổng số Nodes hiện có: {len(all_nodes)}")
    print(f"Tổng số Cụm Liên thông mạnh (SCCs): {len(sccs)}")
    
    if len(sccs) == 1:
        print("✅ KẾT QUẢ TỐT: Đồ thị Liên thông mạnh HOÀN TOÀN.")
        print("   -> Nghĩa là từ một ga bất kỳ, bạn có thể đi tới TẤT CẢ các ga khác và luôn có đường quay về!")
    else:
        print("❌ KẾT QUẢ CÓ LỖI: Đồ thị KHÔNG liên thông mạnh.")
        print("   -> Có ga đi đến được nhưng không có đường về (Bẫy 1 chiều), hoặc bị cô lập.")
        print(f"  -> Cụm Lõi (Mạng lưới chính đi lại 2 chiều tự do): {len(sccs[0])} nodes.")
        print(f"  -> Các Cụm Lỗi / Cô lập: {len(sccs) - 1} cụm.")
        print("\n--- Chi tiết các Cụm Lỗi ---")
        
        for i, comp in enumerate(sccs[1:], 1):
            if len(comp) <= 10:
                nodes_str = ", ".join(comp)
            else:
                nodes_str = ", ".join(comp[:10]) + f" ... (và {len(comp)-10} nodes khác)"
            
            print(f"  [Cụm {i}] Kích thước {len(comp)} nodes | Các nodes: {nodes_str}")
            
    return sccs

if __name__ == "__main__":
    # --- MẪU TEST THỬ LỖI "BẪY 1 CHIỀU" ---
    # Giả sử A nối B, B nối C, C nối A (Cụm liên thông mạnh 1)
    # Nhưng C lại nối sang D, mà D không có đường về (D là cái bẫy)
    adj_map_test = {
        "Ga_A": {"Ga_B": {"weight": 10}},
        "Ga_B": {"Ga_C": {"weight": 10}},
        "Ga_C": {"Ga_A": {"weight": 10}, "Ga_D": {"weight": 5}},
        "Ga_D": {} # D không có đường nối ra ngoài
    }
    
    check_directed_connectivity(adjacency_list)