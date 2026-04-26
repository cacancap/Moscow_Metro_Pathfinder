from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path

# Import thuật toán A* và hàm Heuristic từ thư mục algorithm của bạn
from algorithm.astar import a_star_search

app = FastAPI(title="Moscow Metro Pathfinder API")

# --- 1. THIẾT LẬP ĐƯỜNG DẪN ---
# Sử dụng cấu trúc thư mục từ project của bạn
current_dir = Path(__file__).resolve().parent
stop_dict_coord_path = current_dir / "data" / "processed" / "outputs" / "stop_dict_coord.json"
adjacency_list_path = current_dir / "data" / "processed" / "outputs" / "adjacency_list.json"

# Biến lưu trữ dữ liệu trên RAM để truy xuất nhanh
graph_data = {}
nodes_full_data = {}


# --- 2. TẢI DỮ LIỆU KHI KHỞI ĐỘNG SERVER ---
@app.on_event("startup")
def startup_event():
    global graph_data, nodes_full_data
    print("🚀 Đang tải dữ liệu mạng lưới tàu điện ngầm...")
    try:
        # Đọc file coord để lấy đầy đủ cả Node thật và Fake Node
        with open(stop_dict_coord_path, 'r', encoding='utf-8') as f:
            coord_data = json.load(f)
            # Chuyển đổi sang dạng {ID: data} để A* tra cứu tọa độ
            nodes_full_data = {val['id']: val for val in coord_data.values()}

        with open(adjacency_list_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)

        print(f"✅ Đã tải {len(nodes_full_data)} nodes và dữ liệu đồ thị thành công.")
    except Exception as e:
        print(f"❌ Lỗi khởi động: {e}")


# --- 3. ĐỊNH NGHĨA CẤU TRÚC YÊU CẦU (REQUEST) ---
class PathRequest(BaseModel):
    start_id: str
    target_id: str
    blocked_edges: Optional[List[str]] = []  # Danh sách ID các đoạn đường đang sửa
    blocked_nodes: Optional[List[str]] = []  # Danh sách ID các ga đang đóng cửa


# --- 4. ENDPOINT TÌM ĐƯỜNG ---
@app.post("/find-path")
def find_path(request: PathRequest):
    # Kiểm tra sự tồn tại của ga trong dữ liệu
    if request.start_id not in nodes_full_data:
        raise HTTPException(status_code=400, detail=f"Ga đi (ID: {request.start_id}) không tồn tại.")
    if request.target_id not in nodes_full_data:
        raise HTTPException(status_code=400, detail=f"Ga đến (ID: {request.target_id}) không tồn tại.")

    # Gọi thuật toán A* với đầy đủ các tham số chặn
    path, cost = a_star_search(
        adjacency_list=graph_data,
        nodes_data=nodes_full_data,
        start_node=request.start_id,
        target_node=request.target_id,
        blocked_edges=request.blocked_edges,
        blocked_nodes=request.blocked_nodes
    )

    if path is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lộ trình. Có thể các ga mục tiêu đã bị đóng cửa hoặc đường đi bị phong tỏa."
        )

    # Truy vết danh sách Edge ID để Frontend có thể vẽ lên bản đồ
    path_edges = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_info = graph_data.get(u, {}).get(v, {})
        if isinstance(edge_info, dict) and 'edge_id' in edge_info:
            path_edges.append(edge_info['edge_id'])

    return {
        "status": "success",
        "result": {
            "origin": nodes_full_data[request.start_id].get('name'),
            "destination": nodes_full_data[request.target_id].get('name'),
            "total_distance_meters": round(cost, 2),
            "node_count": len(path),
            "path_nodes": path,
            "path_edges": path_edges
        }
    }


# --- 5. ENDPOINT LẤY DANH SÁCH GA (Dùng cho Dropdown Frontend) ---
@app.get("/stations")
def get_all_stations():
    # Chỉ trả về các ga thật (không lấy fake nodes) để người dùng chọn
    stations = [
        {"id": info["id"], "name": info["name"]}
        for info in nodes_full_data.values()
        if "fake/" not in info["id"]
    ]
    return sorted(stations, key=lambda x: x["name"])