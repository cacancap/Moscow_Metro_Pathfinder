"""
FastAPI server — Moscow Metro Pathfinder
Chạy: python -m uvicorn server:app --reload --port 5000
Sau đó mở: http://127.0.0.1:5000
"""

import json
import math
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from algorithm.graph import load_graph, filter_graph
from algorithm.pathfinder import find_path

# ── Khởi động ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Moscow Metro Pathfinder")

BASE_DIR = Path(__file__).parent

graph, nodes = load_graph()

# Nạp danh sách cạnh (có thông tin tuyến) để phục vụ tính năng cấm tuyến
with open(
    BASE_DIR / "data" / "processed" / "Khanh" / "03_connected_network" / "edges_with_hubs.json",
    encoding="utf-8",
) as f:
    _raw_edges = json.load(f)

# line_index : { line_name: { "colour": str, "edges": set((src, tgt)) } }
line_index: dict = {}
for edge in _raw_edges:
    line = edge.get("line")
    if not line:
        continue
    if line not in line_index:
        line_index[line] = {"colour": edge.get("colour") or "#888888", "edges": set()}
    line_index[line]["edges"].add((edge["source"], edge["target"]))


# ── Helpers ────────────────────────────────────────────────────────────────────

def _nearest_node(lat: float, lon: float) -> str:
    """Trả về node_id gần nhất với tọa độ click trên bản đồ."""
    best_id, best_dist = None, float("inf")
    for node_id, (n_lon, n_lat) in nodes.items():
        d = math.hypot(n_lat - lat, n_lon - lon)
        if d < best_dist:
            best_dist = d
            best_id = node_id
    return best_id


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/api/lines")
def api_lines():
    """
    Trả về danh sách tất cả các tuyến để UI hiển thị checkbox cấm tuyến.

    Response:
    [
        { "name": "Сокольническая линия", "colour": "red" },
        ...
    ]
    """
    return [
        {"name": name, "colour": info["colour"]}
        for name, info in sorted(line_index.items())
    ]


@app.get("/api/path")
def api_path(
    s_lat: float = Query(..., description="Latitude điểm xuất phát"),
    s_lng: float = Query(..., description="Longitude điểm xuất phát"),
    e_lat: float = Query(..., description="Latitude điểm đích"),
    e_lng: float = Query(..., description="Longitude điểm đích"),
    algorithm: str = Query("astar", description="bfs | dijkstra | astar"),
    exclude_lines: List[str] = Query(default=[], description="Danh sách tuyến bị cấm"),
):
    """
    Tìm đường giữa 2 điểm click, có hỗ trợ cấm nhiều tuyến tùy ý.

    Ví dụ cấm 2 tuyến:
    /api/path?s_lat=...&s_lng=...&e_lat=...&e_lng=...
              &exclude_lines=Сокольническая линия
              &exclude_lines=Кольцевая линия

    Response:
    {
        "path":          [[lat, lon], ...],
        "distance_km":   float,
        "num_stations":  int,
        "elapsed_ms":    float,
        "start_id":      str,
        "goal_id":       str,
        "excluded_lines": [str, ...]
    }
    """
    start_id = _nearest_node(s_lat, s_lng)
    goal_id  = _nearest_node(e_lat, e_lng)

    # Gom tất cả cạnh của các tuyến bị cấm thành 1 set
    excluded_edges: set = set()
    invalid_lines = [l for l in exclude_lines if l not in line_index]
    if invalid_lines:
        raise HTTPException(
            status_code=400,
            detail=f"Tuyến không tồn tại: {invalid_lines}. Gọi /api/lines để xem danh sách.",
        )
    for line_name in exclude_lines:
        excluded_edges |= line_index[line_name]["edges"]

    active_graph = filter_graph(graph, excluded_edges) if excluded_edges else graph

    result = find_path(active_graph, nodes, start_id, goal_id, algorithm=algorithm)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm được đường đi. Có thể các tuyến bị cấm đã chặn toàn bộ lộ trình.",
        )

    latlon_path = [[nodes[n][1], nodes[n][0]] for n in result["path"]]

    return {
        "path":           latlon_path,
        "distance_km":    result["distance_km"],
        "num_stations":   result["num_stations"],
        "elapsed_ms":     result["elapsed_ms"],
        "start_id":       start_id,
        "goal_id":        goal_id,
        "excluded_lines": exclude_lines,
    }


# ── Serve file tĩnh ────────────────────────────────────────────────────────────

app.mount("/data",   StaticFiles(directory=str(BASE_DIR / "data")),  name="data")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "web")),   name="static")

@app.get("/")
def index():
    return FileResponse(str(BASE_DIR / "web" / "map.html"))