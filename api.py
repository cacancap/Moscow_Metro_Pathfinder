from __future__ import annotations
import time
from collections import defaultdict
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sqlite3


from algorithm.astar import a_star_search
from algorithm.heuristics import calculate_haversine_distance


app = FastAPI(title="Moscow Metro Pathfinder - A* Only V2")



WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))

# --- BỘ NHỚ ĐỆM RAM (IN-MEMORY CACHE) ---
graph_data = {}
stops_full_data = {}
stations_full_data = {}

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moscow_metro.db")


# --- HÀM NẠP DỮ LIỆU TỪ SQL LÊN RAM ---
def load_metro_network_to_ram():
    global graph_data, stops_full_data, stations_full_data
    print("🔄 Đang đồng bộ mạng lưới Metro từ SQLite vào bộ nhớ RAM...")
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        cursor.execute("SELECT * FROM stations")
        stations_full_data = {}
        for row in cursor.fetchall():
            stations_full_data[row['id']] = {
                "id": row['id'],
                "name": row['name'],
                "name_en": row['name_en'],
                "colour": row['colour'],
                "line_id": row['line_id'],
                "lon": row['lon'],
                "lat": row['lat'],
                "stops": []
            }

        cursor.execute("SELECT * FROM stops WHERE is_blocked = 0")
        stops_full_data = {}
        for row in cursor.fetchall():
            st_id = row['id']
            stops_full_data[st_id] = {
                "id": st_id,
                "station_id": row['station_id'],
                "name": row['name'],
                "lon": row['lon'],
                "lat": row['lat'],
                "line_id": row['line_id'],
                "role": row['role'],
                "colour": row['colour']
            }
            parent_station = row['station_id']
            if parent_station and parent_station in stations_full_data:
                stations_full_data[parent_station]["stops"].append(st_id)

        cursor.execute("""
            SELECT e.* FROM edges e
            JOIN stops s1 ON e.source_id = s1.id
            JOIN stops s2 ON e.dest_id = s2.id
            WHERE e.is_blocked = 0
        """)
        edges_rows = cursor.fetchall()

        new_graph = defaultdict(dict)
        for edge in edges_rows:
            u = edge['source_id']
            v = edge['dest_id']
            new_graph[u][v] = {
                "edge_id": edge['edge_id'],
                "weight": edge['weight'],
                "weight_secs": edge['weight_secs'],
                "line_id": edge['line_id'],
                "edge_type": edge['edge_type']
            }

        graph_data = dict(new_graph)
        db.close()
        print(f"✅ Đã nạp {len(stations_full_data)} ga, {len(stops_full_data)} điểm node và {len(edges_rows)} cạnh nối.")
    except Exception as e:
        print(f"❌ Thất bại: {e}")

@app.on_event("startup")
def startup_event():
    load_metro_network_to_ram()


# =================================================================
#                     CÁC API KHỞI TẠO GIAO DIỆN
# =================================================================

@app.get("/api/network-summary")
def get_network_summary():
    lines = set(st["line_id"] for st in stations_full_data.values() if st["line_id"])
    lines_dict = {line_id: {} for line_id in lines}
    edge_count = sum(len(neighbors) for neighbors in graph_data.values())
    return {
        "station_nodes": len(stops_full_data),
        "edges": edge_count,
        "lines": lines_dict
    }


@app.get("/api/station_list")
def get_station_catalog():
    result = []
    for st in stations_full_data.values():
        result.append({
            "id": st["id"],
            "name": st["name"],
            "name_en": st["name_en"],
            "colour": st["colour"],
            "line_id": [st["line_id"]] if st["line_id"] else [],
            "geometry": [st["lon"], st["lat"]],
            "stops": st["stops"]
        })
    return result


@app.get("/api/stations")
def get_route_stops():
    return list(stops_full_data.values())


@app.get("/api/edge_list")
def get_edge_list():
    result = []
    for u, neighbors in graph_data.items():
        for v, edge_info in neighbors.items():
            result.append({
                "edge_id": edge_info["edge_id"],
                "source_id": u,
                "dest_id": v,
                "weight": edge_info["weight"],
                "weight_secs": edge_info["weight_secs"],
                "line_id": edge_info["line_id"],
                "edge_type": edge_info["edge_type"]
            })
    return result


# =================================================================
#                   LOGIC TÌM ĐƯỜNG VÀ TOẠ ĐỘ
# =================================================================

class StationPathRequest(BaseModel):
    start_station_id: str
    target_station_id: str
    blocked_edges: Optional[List[str]] = []
    blocked_nodes: Optional[List[str]] = []


class CoordinatePathRequest(BaseModel):
    start_lat: float
    start_lon: float
    target_lat: float
    target_lon: float
    blocked_edges: Optional[List[str]] = []
    blocked_nodes: Optional[List[str]] = []


class AdminStatusUpdate(BaseModel):
    target_type: str
    target_id: str
    is_blocked: int



def find_nearest_station_by_first_stop(lat: float, lon: float) -> Optional[str]:
    nearest_station_id = None
    min_distance = float('inf')
    for st_id, st_info in stations_full_data.items():
        stops_list = st_info.get("stops", [])
        if not stops_list:
            continue
        first_stop_id = stops_list[0]
        stop_info = stops_full_data.get(first_stop_id)
        if stop_info:
            dist = calculate_haversine_distance(lon, lat, stop_info['lon'], stop_info['lat'])
            if dist < min_distance:
                min_distance = dist
                nearest_station_id = st_id
    return nearest_station_id


def fetch_geometry_for_path(path_edges: List[str], path_nodes: List[str]) -> List[List[float]]:
    if not path_edges:
        return []
    try:
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        cursor = db.cursor()

        placeholders = ','.join(['?'] * len(path_edges))  # SQLite dùng ? thay vì %s
        cursor.execute(f"""
            SELECT edge_id, seq_order, lon, lat FROM edge_geometries
            WHERE edge_id IN ({placeholders})
            ORDER BY edge_id, seq_order
        """, tuple(path_edges))
        rows = cursor.fetchall()
        db.close()

        geom_map = defaultdict(list)
        for row in rows:
            geom_map[row['edge_id']].append([row['lon'], row['lat']])

        final_geometry = []
        for i, edge_id in enumerate(path_edges):
            segment = geom_map.get(edge_id, [])
            if not segment:
                continue
            target_node_id = path_nodes[i + 1]
            target_node_info = stops_full_data.get(target_node_id)
            if target_node_info:
                target_lon = target_node_info['lon']
                target_lat = target_node_info['lat']
                dist_to_end = calculate_haversine_distance(segment[-1][0], segment[-1][1], target_lon, target_lat)
                dist_to_start = calculate_haversine_distance(segment[0][0], segment[0][1], target_lon, target_lat)
                if dist_to_start < dist_to_end:
                    segment = list(reversed(segment))
            if final_geometry and segment:
                if final_geometry[-1] == segment[0]:
                    final_geometry.extend(segment[1:])
                else:
                    final_geometry.extend(segment)
            else:
                final_geometry.extend(segment)

        return final_geometry
    except Exception as e:
        print(f"⚠️ Lỗi geometry: {e}")
        return []

def execute_routing(start_stop_id: str, target_stop_id: str, b_edges: list, b_nodes: list):
    started_at = time.perf_counter()

    # CHỈ DÙNG DUY NHẤT A*
    path, cost = a_star_search(
        adjacency_list=graph_data,
        nodes_data=stops_full_data,
        start_node=start_stop_id,
        target_node=target_stop_id,
        blocked_edges=b_edges,
        blocked_nodes=b_nodes
    )

    elapsed_ms = (time.perf_counter() - started_at) * 1000

    if path is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy lộ trình. Vui lòng thử lại.")

    path_edges = []
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        edge_info = graph_data.get(u, {}).get(v, {})
        if isinstance(edge_info, dict) and 'edge_id' in edge_info:
            path_edges.append(edge_info['edge_id'])

    route_geometry = fetch_geometry_for_path(path_edges, path)

    return {
        "status": "success",
        "algorithm_used": "astar",
        "elapsed_ms": round(elapsed_ms, 2),
        "result": {
            "origin_node_id": start_stop_id,
            "origin_node_name": stops_full_data.get(start_stop_id, {}).get('name', 'Unknown'),
            "destination_node_id": target_stop_id,
            "destination_node_name": stops_full_data.get(target_stop_id, {}).get('name', 'Unknown'),
            "total_cost_meters_or_secs": round(cost, 2),
            "node_count": len(path),
            "path_nodes": path,
            "path_edges": path_edges,
            "geometry_polyline": route_geometry
        }
    }


# =================================================================
#                     CÁC API ENDPOINTS CHÍNH
# =================================================================

@app.get("/api/nearest-station")
def get_nearest_station(lat: float, lon: float):
    nearest_id = None
    min_dist = float('inf')

    for st_id, st_info in stations_full_data.items():
        stops = st_info.get("stops", [])
        if not stops:
            continue
        stop = stops_full_data.get(stops[0])
        if not stop:
            continue
        dist = calculate_haversine_distance(lon, lat, stop['lon'], stop['lat'])
        if dist < min_dist:
            min_dist = dist
            nearest_id = st_id

    if not nearest_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy ga.")

    st = stations_full_data[nearest_id]
    stop = stops_full_data.get(st['stops'][0], {})
    return {
        "id": nearest_id,
        "name": st["name"],
        "name_en": st.get("name_en", ""),
        "distance_meters": round(min_dist, 2),
        "lat": stop.get("lat"),
        "lon": stop.get("lon"),
    }

@app.post("/api/path/by-stations")
def find_path_by_station_ids(payload: StationPathRequest):
    start_st = stations_full_data.get(payload.start_station_id)
    target_st = stations_full_data.get(payload.target_station_id)

    if not start_st or not target_st or not start_st['stops'] or not target_st['stops']:
        raise HTTPException(status_code=400, detail="Mã Ga tổng không tồn tại hoặc ga chưa có điểm dừng.")

    return execute_routing(
        start_stop_id=start_st['stops'][0],
        target_stop_id=target_st['stops'][0],
        b_edges=payload.blocked_edges,
        b_nodes=payload.blocked_nodes
    )


@app.post("/api/path/by-coordinates")
def find_path_by_map_coordinates(payload: CoordinatePathRequest):
    start_station_id = find_nearest_station_by_first_stop(payload.start_lat, payload.start_lon)
    target_station_id = find_nearest_station_by_first_stop(payload.target_lat, payload.target_lon)

    if not start_station_id or not target_station_id:
        raise HTTPException(status_code=404, detail="Không tìm thấy ga tàu nào gần tọa độ này.")

    start_stop = stations_full_data[start_station_id]['stops'][0]
    target_stop = stations_full_data[target_station_id]['stops'][0]

    response = execute_routing(
        start_stop_id=start_stop,
        target_stop_id=target_stop,
        b_edges=payload.blocked_edges,
        b_nodes=payload.blocked_nodes
    )

    response["nearest_info"] = {
        "start_station_id": start_station_id,
        "start_station_name": stations_full_data[start_station_id]["name"],
        "target_station_id": target_station_id,
        "target_station_name": stations_full_data[target_station_id]["name"]
    }
    return response

@app.post("/api/admin/network/status")
def admin_update_network_status(payload: AdminStatusUpdate):
    t_type = payload.target_type.lower()
    if t_type not in ["station", "stop", "edge"]:
        raise HTTPException(status_code=400, detail="target_type không hợp lệ.")

    table_name = "stations" if t_type == "station" else ("stops" if t_type == "stop" else "edges")
    id_column = "id" if t_type != "edge" else "edge_id"

    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    try:
        cursor.execute(
            f"UPDATE {table_name} SET is_blocked = ? WHERE {id_column} = ?",
            (payload.is_blocked, payload.target_id)
        )
        db.commit()
        row_affected = cursor.rowcount
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi SQLite: {str(e)}")
    finally:
        cursor.close()
        db.close()

    if row_affected == 0:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy ID '{payload.target_id}'.")

    load_metro_network_to_ram()

    status_text = "Chặn" if payload.is_blocked == 1 else "Mở khóa"
    return {"status": "success", "message": f"Admin đã {status_text} thành công {t_type}."}


@app.get("/{filename}")
def serve_static(filename: str):
    file_path = os.path.join(WEB_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")