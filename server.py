"""
Unified FastAPI app for Moscow Metro Pathfinder.

Run:
    python -m uvicorn server:app --reload --host 127.0.0.1 --port 5000

Open:
    http://127.0.0.1:5000
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
import sqlite3

from algorithm.astar import a_star_search
from algorithm.dijkstra import dijkstra_search
from algorithm.bfs import bfs_search


BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
DATA_OUTPUT_DIR = BASE_DIR / "data" / "processed" / "outputs"
DB_PATH = BASE_DIR / "moscow_metro.db"



class PathRequest(BaseModel):
    start_id: str
    target_id: str
    algorithm: str = "astar"          # "astar", "dijkstra", or "bfs"
    blocked_edges: Optional[list[str]] = []
    blocked_nodes: Optional[list[str]] = []


class BombRequest(BaseModel):
    lat: float
    lon: float
    radius_meters: float


# ▶ MODEL MỚI: nhận danh sách block/unblock từ frontend
class SetBlockedRequest(BaseModel):
    blocked_nodes: list[str] = []     # stop IDs cần block
    blocked_edges: list[str] = []     # edge IDs cần block
    unblocked_nodes: list[str] = []   # stop IDs cần unblock
    unblocked_edges: list[str] = []   # edge IDs cần unblock



DB_CACHE: dict[str, Any] = {
    "coord_data": {},
    "station_data": {},
    "edge_list": [],
    "adjacency_list": {},
    "way_to_line": {},
    "default_blocked_nodes": set(),   # set[str] — stop IDs
    "default_blocked_edges": set(),   # set[str] — edge IDs
}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # cho phép đọc/ghi đồng thời
    return conn


def fetch_data_from_db() -> None:
    """Load toàn bộ dữ liệu mạng lưới + trạng thái blocked từ DB vào RAM."""
    conn = _get_conn()
    cursor = conn.cursor()

    try:
        # 1. Build coord_data (Stops)
        cursor.execute("SELECT id, lat, lon, name FROM stops")
        DB_CACHE["coord_data"] = {row["id"]: dict(row) for row in cursor.fetchall()}

        # 2. Build station_data
        cursor.execute("SELECT id, name, name_en, colour, line_id FROM stations")
        stations = {row["id"]: dict(row) for row in cursor.fetchall()}

        cursor.execute("SELECT station_id, id AS stop_id FROM stops WHERE station_id IS NOT NULL")
        for row in cursor.fetchall():
            if row["station_id"] in stations:
                if "stops" not in stations[row["station_id"]]:
                    stations[row["station_id"]]["stops"] = []
                stations[row["station_id"]]["stops"].append(row["stop_id"])

        for st_id, st_info in stations.items():
            if st_info.get("stops"):
                first_stop_id = st_info["stops"][0]
                if first_stop_id in DB_CACHE["coord_data"]:
                    stop_info = DB_CACHE["coord_data"][first_stop_id]
                    st_info["geometry"] = [stop_info["lon"], stop_info["lat"]]
            else:
                st_info["geometry"] = []

        DB_CACHE["station_data"] = stations

        # 3. Build edge_list + geometry
        cursor.execute("SELECT edge_id, source_id, dest_id, line_id, weight FROM edges")
        edges = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            "SELECT edge_id, lon, lat FROM edge_geometry ORDER BY edge_id, point_order"
        )
        geometry_map: dict[str, list] = {}
        for row in cursor.fetchall():
            geometry_map.setdefault(row["edge_id"], []).append([row["lon"], row["lat"]])

        stop_to_colour: dict[str, str] = {}
        for station in stations.values():
            colour = station.get("colour", "")
            for stop_id in station.get("stops", []):
                stop_to_colour[stop_id] = colour

        for edge in edges:
            edge["colour"] = (
                stop_to_colour.get(edge["source_id"])
                or stop_to_colour.get(edge["dest_id"])
                or ""
            )
            edge["geometry"] = geometry_map.get(edge["edge_id"], [])

        DB_CACHE["edge_list"] = edges

        # 4. Build adjacency_list
        adjacency: dict[str, dict] = {}
        for edge in edges:
            src = edge["source_id"]
            adjacency.setdefault(src, {})[edge["dest_id"]] = {
                "weight": edge["weight"],
                "edge_id": edge["edge_id"],
            }
        DB_CACHE["adjacency_list"] = adjacency

        # 5. Build way_to_line
        cursor.execute("SELECT way_id, line_id FROM way_to_line")
        DB_CACHE["way_to_line"] = {row["way_id"]: row["line_id"] for row in cursor.fetchall()}

        try:
            cursor.execute("SELECT id FROM stops WHERE is_blocked = 1")
            DB_CACHE["default_blocked_nodes"] = {row["id"] for row in cursor.fetchall()}

            cursor.execute("SELECT edge_id FROM edges WHERE is_blocked = 1")
            DB_CACHE["default_blocked_edges"] = {row["edge_id"] for row in cursor.fetchall()}

            print(
                f"  Blocked từ DB: "
                f"{len(DB_CACHE['default_blocked_nodes'])} node, "
                f"{len(DB_CACHE['default_blocked_edges'])} edge"
            )
        except Exception as exc:
            # Cột is_blocked chưa tồn tại — bỏ qua, chạy migration trước
            print(f"  [WARN] Chưa có cột is_blocked ({exc}). Chạy migrate_add_is_blocked.py trước.")
            DB_CACHE["default_blocked_nodes"] = set()
            DB_CACHE["default_blocked_edges"] = set()

    finally:
        conn.close()


def _coord_data() -> dict[str, dict[str, Any]]:
    return DB_CACHE["coord_data"]

def _adjacency_data() -> dict[str, dict[str, Any]]:
    return DB_CACHE["adjacency_list"]

def _station_data() -> dict[str, dict[str, Any]]:
    return DB_CACHE["station_data"]

def _edge_data() -> list[dict[str, Any]]:
    return DB_CACHE["edge_list"]

def _way_to_line_data() -> dict[str, Any]:
    return DB_CACHE["way_to_line"]



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Đang tải mạng lưới ga tàu từ Database lên RAM...")
    fetch_data_from_db()
    print("Sẵn sàng!")
    yield


app = FastAPI(title="Moscow Metro Pathfinder", lifespan=lifespan)

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    traceback.print_exc()
    return JSONResponse({"error": str(exc)}, status_code=500)


def _route_stations() -> list[dict[str, str]]:
    stations = [
        {"id": info["id"], "name": info.get("name", info["id"])}
        for info in _coord_data().values()
        if "fake/" not in info["id"]
    ]
    return sorted(stations, key=lambda item: item["name"])


def _station_catalog() -> list[dict[str, Any]]:
    station_list = []
    for station_id, station in _station_data().items():
        station_list.append({
            "id": station_id,
            "name": station.get("name", ""),
            "name_en": station.get("name_en", ""),
            "colour": station.get("colour", ""),
            "line_id": station.get("line_id", ""),
            "geometry": station.get("geometry", []),
            "stops": station.get("stops", []),
        })
    return sorted(station_list, key=lambda item: (str(item["line_id"]), item["name"]))


def _line_summary() -> dict[str, int]:
    summary: dict[str, int] = {}
    for edge in _edge_data():
        line_id = str(edge.get("line_id") or "unknown")
        summary[line_id] = summary.get(line_id, 0) + 1
    return dict(sorted(summary.items(), key=lambda item: item[0]))


def _path_edge_ids(path_nodes: list[str]) -> list[str]:
    graph = _adjacency_data()
    path_edges = []
    for index in range(len(path_nodes) - 1):
        source = path_nodes[index]
        target = path_nodes[index + 1]
        edge_info = graph.get(source, {}).get(target, {})
        if isinstance(edge_info, dict) and edge_info.get("edge_id"):
            path_edges.append(edge_info["edge_id"])
    return path_edges



@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/map.html")


@app.get("/api/health")
def health_check():
    try:
        _coord_data()
        _adjacency_data()
        _station_data()
        _edge_data()
    except Exception as exc:
        return JSONResponse(
            {"status": "error", "data_source": str(DATA_OUTPUT_DIR), "error": str(exc)},
            status_code=500,
        )
    return {
        "status": "ok",
        "data_source": str(DATA_OUTPUT_DIR),
        "station_nodes": len(_route_stations()),
        "station_groups": len(_station_data()),
        "edges": len(_edge_data()),
    }


@app.get("/api/network-summary")
def get_network_summary():
    try:
        return {
            "data_source": str(DATA_OUTPUT_DIR),
            "station_nodes": len(_route_stations()),
            "station_groups": len(_station_data()),
            "edges": len(_edge_data()),
            "lines": _line_summary(),
            "ways": len(_way_to_line_data()),
        }
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/edge_list")
def get_edge_list():
    try:
        return JSONResponse(_edge_data())
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/station_list")
def get_station_list():
    try:
        return JSONResponse(_station_catalog())
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/stations")
def get_route_stations():
    try:
        return JSONResponse(_route_stations())
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/nearest-station")
def get_nearest_station(lat: float, lon: float):
    try:
        from algorithm.heuristics import calculate_haversine_distance

        coords_data = _coord_data()
        station_data = _station_data()
        nearest_station = None
        min_distance = float("infinity")

        for station_id, station in station_data.items():
            if not station.get("stops") or not station.get("geometry"):
                continue
            first_stop_id = station["stops"][0]
            if first_stop_id not in coords_data:
                continue
            stop_info = coords_data[first_stop_id]
            stop_lon = stop_info.get("lon")
            stop_lat = stop_info.get("lat")
            if stop_lon is None or stop_lat is None:
                continue
            distance = calculate_haversine_distance(lon, lat, stop_lon, stop_lat)
            if distance < min_distance:
                min_distance = distance
                nearest_station = {
                    "id": station_id,
                    "name": station.get("name", ""),
                    "name_en": station.get("name_en", ""),
                    "distance_meters": round(distance, 2),
                    "lat": stop_lat,
                    "lon": stop_lon,
                }

        if nearest_station is None:
            return JSONResponse({"error": "No station found"}, status_code=404)
        return JSONResponse(nearest_station)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)



@app.get("/api/admin/blocked")
def get_blocked():
    """
    Trả về danh sách node và edge đang bị block trong DB.
    Frontend dùng để khởi tạo / đồng bộ lại localStorage khi load trang.
    """
    return JSONResponse({
        "blocked_nodes": sorted(DB_CACHE["default_blocked_nodes"]),
        "blocked_edges": sorted(DB_CACHE["default_blocked_edges"]),
    })



@app.post("/api/admin/set-blocked")
def set_blocked(payload: SetBlockedRequest):
    """
    Nhận danh sách node/edge cần block hoặc unblock từ frontend.
    - Ghi is_blocked vào DB
    - Cập nhật DB_CACHE["default_blocked_nodes/edges"] ngay lập tức
    - Không cần reload toàn bộ cache
    """
    conn = _get_conn()
    cur = conn.cursor()

    try:
        # --- Block nodes ---
        if payload.blocked_nodes:
            cur.executemany(
                "UPDATE stops SET is_blocked = 1 WHERE id = ?",
                [(node_id,) for node_id in payload.blocked_nodes],
            )
            DB_CACHE["default_blocked_nodes"].update(payload.blocked_nodes)

        # --- Block edges ---
        if payload.blocked_edges:
            cur.executemany(
                "UPDATE edges SET is_blocked = 1 WHERE edge_id = ?",
                [(edge_id,) for edge_id in payload.blocked_edges],
            )
            DB_CACHE["default_blocked_edges"].update(payload.blocked_edges)

        # --- Unblock nodes ---
        if payload.unblocked_nodes:
            cur.executemany(
                "UPDATE stops SET is_blocked = 0 WHERE id = ?",
                [(node_id,) for node_id in payload.unblocked_nodes],
            )
            DB_CACHE["default_blocked_nodes"].difference_update(payload.unblocked_nodes)

        # --- Unblock edges ---
        if payload.unblocked_edges:
            cur.executemany(
                "UPDATE edges SET is_blocked = 0 WHERE edge_id = ?",
                [(edge_id,) for edge_id in payload.unblocked_edges],
            )
            DB_CACHE["default_blocked_edges"].difference_update(payload.unblocked_edges)

        conn.commit()

        return JSONResponse({
            "status": "ok",
            "blocked_nodes_total": len(DB_CACHE["default_blocked_nodes"]),
            "blocked_edges_total": len(DB_CACHE["default_blocked_edges"]),
        })

    except Exception as exc:
        conn.rollback()
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        conn.close()



@app.post("/api/admin/bomb-closure")
def admin_bomb_closure(payload: BombRequest):
    try:
        from algorithm.heuristics import calculate_haversine_distance

        coords_data = _coord_data()
        station_data = _station_data()
        edge_data = _edge_data()

        blocked_nodes: set[str] = set()
        blocked_edges: set[str] = set()

        for station in station_data.values():
            if not station.get("stops") or not station.get("geometry"):
                continue
            first_stop_id = station["stops"][0]
            if first_stop_id not in coords_data:
                continue
            stop_info = coords_data[first_stop_id]
            stop_lon = stop_info.get("lon")
            stop_lat = stop_info.get("lat")
            if stop_lon is None or stop_lat is None:
                continue
            distance = calculate_haversine_distance(payload.lon, payload.lat, stop_lon, stop_lat)
            if distance > payload.radius_meters:
                continue
            for stop_id in station["stops"]:
                if stop_id in coords_data:
                    blocked_nodes.add(stop_id)

        for edge in edge_data:
            source_id = edge.get("source_id")
            dest_id = edge.get("dest_id")
            edge_id = edge.get("edge_id")
            if not edge_id or not source_id or not dest_id:
                continue
            if source_id in blocked_nodes or dest_id in blocked_nodes:
                blocked_edges.add(edge_id)

        return JSONResponse({
            "blocked_nodes": sorted(blocked_nodes),
            "blocked_edges": sorted(blocked_edges),
            "blocked_node_count": len(blocked_nodes),
            "blocked_edge_count": len(blocked_edges),
        })
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/find-path")
def find_path(payload: PathRequest):
    nodes = _coord_data()
    graph = _adjacency_data()

    if payload.start_id not in nodes:
        raise HTTPException(status_code=400, detail=f"Ga đi (ID: {payload.start_id}) không tồn tại.")
    if payload.target_id not in nodes:
        raise HTTPException(status_code=400, detail=f"Ga đến (ID: {payload.target_id}) không tồn tại.")


    effective_blocked_nodes = list(
        set(payload.blocked_nodes or []) | DB_CACHE["default_blocked_nodes"]
    )
    effective_blocked_edges = list(
        set(payload.blocked_edges or []) | DB_CACHE["default_blocked_edges"]
    )

    started_at = time.perf_counter()

    algorithm = payload.algorithm.lower() if payload.algorithm else "astar"

    if algorithm == "dijkstra":
        path, cost = dijkstra_search(
            adjacency_list=graph,
            nodes_data=nodes,
            start_node=payload.start_id,
            target_node=payload.target_id,
            blocked_edges=effective_blocked_edges,
            blocked_nodes=effective_blocked_nodes,
        )
    elif algorithm == "bfs":
        path, cost = bfs_search(
            adjacency_list=graph,
            nodes_data=nodes,
            start_node=payload.start_id,
            target_node=payload.target_id,
            blocked_edges=effective_blocked_edges,
            blocked_nodes=effective_blocked_nodes,
        )
    else:
        path, cost = a_star_search(
            adjacency_list=graph,
            nodes_data=nodes,
            start_node=payload.start_id,
            target_node=payload.target_id,
            blocked_edges=effective_blocked_edges,
            blocked_nodes=effective_blocked_nodes,
        )

    elapsed_ms = (time.perf_counter() - started_at) * 1000

    if path is None:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy lộ trình. Có thể ga đã đóng hoặc các đoạn nối đang bị chặn.",
        )

    return {
        "status": "success",
        "result": {
            "origin": nodes[payload.start_id].get("name"),
            "destination": nodes[payload.target_id].get("name"),
            "total_distance_meters": round(cost, 2),
            "node_count": len(path),
            "elapsed_ms": round(elapsed_ms, 2),
            "path_nodes": path,
            "path_edges": _path_edge_ids(path),
        },
    }



app.mount("/data", StaticFiles(directory=str(BASE_DIR / "data")), name="data")
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=False), name="web")
