from __future__ import annotations

import json
import os
import sys
import time
from functools import lru_cache

from flask import Flask, jsonify, request, send_from_directory

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "processed", "outputs")
STOP_DICT_COORD_PATH = os.path.join(DATA_OUTPUT_DIR, "stop_dict_coord.json")
ADJACENCY_LIST_PATH = os.path.join(DATA_OUTPUT_DIR, "adjacency_list.json")
STATION_DICT_PATH = os.path.join(DATA_OUTPUT_DIR, "station_dict.json")
EDGE_LIST_PATH = os.path.join(DATA_OUTPUT_DIR, "edge_list.json")
WAY_TO_LINE_PATH = os.path.join(DATA_OUTPUT_DIR, "way_to_line.json")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithm.astar import a_star_search


app = Flask(__name__, static_folder=".")


def _load_json(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing data file: {path}")

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache(maxsize=1)
def _coord_data():
    raw = _load_json(STOP_DICT_COORD_PATH)
    return {value["id"]: value for value in raw.values()}


@lru_cache(maxsize=1)
def _adjacency_data():
    return _load_json(ADJACENCY_LIST_PATH)


@lru_cache(maxsize=1)
def _station_data():
    return _load_json(STATION_DICT_PATH)


@lru_cache(maxsize=1)
def _edge_data():
    return _load_json(EDGE_LIST_PATH)


@lru_cache(maxsize=1)
def _way_to_line_data():
    if not os.path.exists(WAY_TO_LINE_PATH):
        return {}
    return _load_json(WAY_TO_LINE_PATH)


def _route_stations():
    stations = [
        {"id": info["id"], "name": info.get("name", info["id"])}
        for info in _coord_data().values()
        if "fake/" not in info["id"]
    ]
    return sorted(stations, key=lambda item: item["name"])


def _station_catalog():
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


def _line_summary():
    summary = {}
    for edge in _edge_data():
        line_id = str(edge.get("line_id") or "unknown")
        summary[line_id] = summary.get(line_id, 0) + 1
    return dict(sorted(summary.items(), key=lambda item: item[0]))


def _path_edge_ids(path_nodes):
    graph = _adjacency_data()
    path_edges = []

    for index in range(len(path_nodes) - 1):
        source = path_nodes[index]
        target = path_nodes[index + 1]
        edge_info = graph.get(source, {}).get(target, {})
        if isinstance(edge_info, dict) and edge_info.get("edge_id"):
            path_edges.append(edge_info["edge_id"])

    return path_edges


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(".", filename)


@app.route("/api/health")
def health_check():
    try:
        _coord_data()
        _adjacency_data()
        _station_data()
        _edge_data()
    except Exception as exc:
        return jsonify({
            "status": "error",
            "data_source": DATA_OUTPUT_DIR,
            "error": str(exc),
        }), 500

    return jsonify({
        "status": "ok",
        "data_source": DATA_OUTPUT_DIR,
        "station_nodes": len(_route_stations()),
        "station_groups": len(_station_data()),
        "edges": len(_edge_data()),
    })


@app.route("/api/network-summary")
def get_network_summary():
    try:
        return jsonify({
            "data_source": DATA_OUTPUT_DIR,
            "station_nodes": len(_route_stations()),
            "station_groups": len(_station_data()),
            "edges": len(_edge_data()),
            "lines": _line_summary(),
            "ways": len(_way_to_line_data()),
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/edge_list")
def get_edge_list():
    try:
        return jsonify(_edge_data())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/station_list")
def get_station_list():
    try:
        return jsonify(_station_catalog())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/stations")
def get_all_stations():
    try:
        return jsonify(_route_stations())
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/find-path", methods=["POST"])
def find_path():
    payload = request.get_json(silent=True) or {}
    nodes = _coord_data()
    graph = _adjacency_data()

    start_id = payload.get("start_id")
    target_id = payload.get("target_id")
    blocked_edges = payload.get("blocked_edges") or []
    blocked_nodes = payload.get("blocked_nodes") or []

    if start_id not in nodes:
        return jsonify({"detail": f"Ga đi (ID: {start_id}) không tồn tại."}), 400
    if target_id not in nodes:
        return jsonify({"detail": f"Ga đến (ID: {target_id}) không tồn tại."}), 400

    started_at = time.perf_counter()
    path, cost = a_star_search(
        adjacency_list=graph,
        nodes_data=nodes,
        start_node=start_id,
        target_node=target_id,
        blocked_edges=blocked_edges,
        blocked_nodes=blocked_nodes,
    )
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    if path is None:
        return jsonify({
            "detail": "Không tìm thấy lộ trình. Có thể ga đã đóng hoặc các đoạn nối đang bị chặn."
        }), 404

    return jsonify({
        "status": "success",
        "result": {
            "origin": nodes[start_id].get("name"),
            "destination": nodes[target_id].get("name"),
            "total_distance_meters": round(cost, 2),
            "node_count": len(path),
            "elapsed_ms": round(elapsed_ms, 2),
            "path_nodes": path,
            "path_edges": _path_edge_ids(path),
        },
    })


if __name__ == "__main__":
    print("Moscow Metro Pathfinder")
    print("=" * 50)
    print(f"Data source: {DATA_OUTPUT_DIR}")
    print("Web server: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
