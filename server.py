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
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from algorithm.astar import a_star_search
from algorithm.dijkstra import dijkstra_search
from algorithm.bfs import bfs_search


app = FastAPI(title="Moscow Metro Pathfinder")

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
DATA_OUTPUT_DIR = BASE_DIR / "data" / "processed" / "outputs"

STOP_DICT_COORD_PATH = DATA_OUTPUT_DIR / "stop_dict_coord.json"
ADJACENCY_LIST_PATH = DATA_OUTPUT_DIR / "adjacency_list.json"
STATION_DICT_PATH = DATA_OUTPUT_DIR / "station_dict.json"
EDGE_LIST_PATH = DATA_OUTPUT_DIR / "edge_list.json"
WAY_TO_LINE_PATH = DATA_OUTPUT_DIR / "way_to_line.json"


class PathRequest(BaseModel):
    start_id: str
    target_id: str
    algorithm: str = "astar"  # "astar", "dijkstra", or "bfs"
    blocked_edges: Optional[list[str]] = []
    blocked_nodes: Optional[list[str]] = []


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache(maxsize=1)
def _coord_data() -> dict[str, dict[str, Any]]:
    raw = _load_json(STOP_DICT_COORD_PATH)
    return {value["id"]: value for value in raw.values()}


@lru_cache(maxsize=1)
def _adjacency_data() -> dict[str, dict[str, Any]]:
    return _load_json(ADJACENCY_LIST_PATH)


@lru_cache(maxsize=1)
def _station_data() -> dict[str, dict[str, Any]]:
    return _load_json(STATION_DICT_PATH)


@lru_cache(maxsize=1)
def _edge_data() -> list[dict[str, Any]]:
    return _load_json(EDGE_LIST_PATH)


@lru_cache(maxsize=1)
def _way_to_line_data() -> dict[str, Any]:
    if not WAY_TO_LINE_PATH.exists():
        return {}
    return _load_json(WAY_TO_LINE_PATH)


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
app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
