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
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
import sqlite3
from pathlib import Path

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
    algorithm: str = "astar"  # "astar", "dijkstra", or "bfs"
    blocked_edges: Optional[list[str]] = []
    blocked_nodes: Optional[list[str]] = []


class BombRequest(BaseModel):
    lat: float
    lon: float
    radius_meters: float

# Biến lưu trữ in-memory cache
DB_CACHE = {
    "coord_data": {},
    "station_data": {},
    "edge_list": [],
    "adjacency_list": {},
    "way_to_line": {}
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Đang tải mạng lưới ga tàu từ Database lên RAM...")
    fetch_data_from_db()
    print("Sẵn sàng!")
    yield


app = FastAPI(title="Moscow Metro Pathfinder", lifespan=lifespan)

def fetch_data_from_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Build _coord_data (Stops)
        cursor.execute("SELECT id, lat, lon, name FROM stops")
        DB_CACHE["coord_data"] = {row["id"]: dict(row) for row in cursor.fetchall()}

        # 2. Build _station_data
        cursor.execute("SELECT id, name, name_en, colour, line_id FROM stations")
        stations = {row["id"]: dict(row) for row in cursor.fetchall()}

        # Query gộp stops vào station
        cursor.execute("SELECT station_id, id AS stop_id FROM stops WHERE station_id IS NOT NULL")
        for row in cursor.fetchall():
            if row["station_id"] in stations:  # Thêm check để tránh lỗi KeyError nếu data lệch
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

        # 3. Build _edge_list và gom Edge_Geometry lại (Reverse 1NF về Object cho thuật toán)
        cursor.execute("SELECT edge_id, source_id, dest_id, line_id, weight FROM edges")
        edges = [dict(row) for row in cursor.fetchall()]

        # Gom mảng tọa độ
        cursor.execute("SELECT edge_id, lon, lat FROM edge_geometry ORDER BY edge_id, point_order")
        geometry_map = {}
        for row in cursor.fetchall():
            if row["edge_id"] not in geometry_map:
                geometry_map[row["edge_id"]] = []
            geometry_map[row["edge_id"]].append([row["lon"], row["lat"]])

        for edge in edges:
            edge["geometry"] = geometry_map.get(edge["edge_id"], [])

        DB_CACHE["edge_list"] = edges

        # 4. Tự động Build _adjacency_list từ edges
        adjacency = {}
        for edge in edges:
            src = edge["source_id"]
            if src not in adjacency:
                adjacency[src] = {}
            adjacency[src][edge["dest_id"]] = {"weight": edge["weight"], "edge_id": edge["edge_id"]}
        DB_CACHE["adjacency_list"] = adjacency

        # 5. Build way_to_line
        cursor.execute("SELECT way_id, line_id FROM way_to_line")
        DB_CACHE["way_to_line"] = {row["way_id"]: row["line_id"] for row in cursor.fetchall()}

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


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/map.html")

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
        station_list.append(
            {
                "id": station_id,
                "name": station.get("name", ""),
                "name_en": station.get("name_en", ""),
                "colour": station.get("colour", ""),
                "line_id": station.get("line_id", ""),
                "geometry": station.get("geometry", []),
                "stops": station.get("stops", []),
            }
        )
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


@app.get("/api/health")
def health_check():
    try:
        _coord_data()
        _adjacency_data()
        _station_data()
        _edge_data()
    except Exception as exc:
        return JSONResponse(
            {
                "status": "error",
                "data_source": str(DATA_OUTPUT_DIR),
                "error": str(exc),
            },
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
    """Find nearest station from coordinates (lat, lon)"""
    try:
        from algorithm.heuristics import calculate_haversine_distance
        
        coords_data = _coord_data()
        station_data = _station_data()
        
        # Find nearest real station (not fake nodes)
        nearest_station = None
        min_distance = float('infinity')
        
        for station_id, station in station_data.items():
            # Skip if station has no stops or coordinates
            if not station.get('stops') or not station.get('geometry'):
                continue
            
            # Use first stop to get coordinates
            first_stop_id = station['stops'][0]
            if first_stop_id not in coords_data:
                continue
            
            stop_info = coords_data[first_stop_id]
            stop_lon = stop_info.get('lon')
            stop_lat = stop_info.get('lat')
            
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

        return JSONResponse(
            {
                "blocked_nodes": sorted(blocked_nodes),
                "blocked_edges": sorted(blocked_edges),
                "blocked_node_count": len(blocked_nodes),
                "blocked_edge_count": len(blocked_edges),
            }
        )
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

    started_at = time.perf_counter()
    
    # Route to appropriate algorithm
    algorithm = payload.algorithm.lower() if payload.algorithm else "astar"
    if algorithm == "dijkstra":
        path, cost = dijkstra_search(
            adjacency_list=graph,
            nodes_data=nodes,
            start_node=payload.start_id,
            target_node=payload.target_id,
            blocked_edges=payload.blocked_edges or [],
            blocked_nodes=payload.blocked_nodes or [],
        )
    elif algorithm == "bfs":
        path, cost = bfs_search(
            adjacency_list=graph,
            nodes_data=nodes,
            start_node=payload.start_id,
            target_node=payload.target_id,
            blocked_edges=payload.blocked_edges or [],
            blocked_nodes=payload.blocked_nodes or [],
        )
    else:  # default to astar
        path, cost = a_star_search(
            adjacency_list=graph,
            nodes_data=nodes,
            start_node=payload.start_id,
            target_node=payload.target_id,
            blocked_edges=payload.blocked_edges or [],
            blocked_nodes=payload.blocked_nodes or [],
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
