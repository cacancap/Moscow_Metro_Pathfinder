from flask import Flask, Response, jsonify, request, send_from_directory
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_ROOT = "http://127.0.0.1:8000"
STOP_DICT_COORD_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "outputs", "stop_dict_coord.json")
ADJACENCY_LIST_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "outputs", "adjacency_list.json")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from algorithm.astar import a_star_search


app = Flask(__name__, static_folder=".")

GRAPH_DATA = None
NODES_FULL_DATA = None


def _proxy_json(path, method="GET", body=None):
    url = f"{API_ROOT}{path}"
    headers = {"User-Agent": "Mozilla/5.0"}
    if body is not None:
        headers["Content-Type"] = "application/json"

    request_obj = Request(url, data=body, headers=headers, method=method)
    with urlopen(request_obj, timeout=15) as response:
        payload = response.read()
        return Response(payload, status=response.getcode(), content_type="application/json")


def _ensure_local_graph_loaded():
    global GRAPH_DATA, NODES_FULL_DATA

    if GRAPH_DATA is not None and NODES_FULL_DATA is not None:
        return

    with open(STOP_DICT_COORD_PATH, "r", encoding="utf-8") as file:
        coord_data = json.load(file)
        NODES_FULL_DATA = {value["id"]: value for value in coord_data.values()}

    with open(ADJACENCY_LIST_PATH, "r", encoding="utf-8") as file:
        GRAPH_DATA = json.load(file)


def _load_station_fallback():
    _ensure_local_graph_loaded()
    stations = [
        {"id": info["id"], "name": info["name"]}
        for info in NODES_FULL_DATA.values()
        if "fake/" not in info["id"]
    ]
    return sorted(stations, key=lambda item: item["name"])


def _find_path_local(payload):
    _ensure_local_graph_loaded()

    start_id = payload.get("start_id")
    target_id = payload.get("target_id")
    blocked_edges = payload.get("blocked_edges") or []
    blocked_nodes = payload.get("blocked_nodes") or []

    if start_id not in NODES_FULL_DATA:
        return jsonify({"detail": f"Ga đi (ID: {start_id}) không tồn tại."}), 400
    if target_id not in NODES_FULL_DATA:
        return jsonify({"detail": f"Ga đến (ID: {target_id}) không tồn tại."}), 400

    path, cost = a_star_search(
        adjacency_list=GRAPH_DATA,
        nodes_data=NODES_FULL_DATA,
        start_node=start_id,
        target_node=target_id,
        blocked_edges=blocked_edges,
        blocked_nodes=blocked_nodes,
    )

    if path is None:
        return jsonify({
            "detail": "Không tìm thấy lộ trình. Có thể các ga mục tiêu đã bị đóng cửa hoặc đường đi bị phong tỏa."
        }), 404

    path_edges = []
    for index in range(len(path) - 1):
        source = path[index]
        target = path[index + 1]
        edge_info = GRAPH_DATA.get(source, {}).get(target, {})
        if isinstance(edge_info, dict) and "edge_id" in edge_info:
            path_edges.append(edge_info["edge_id"])

    return jsonify({
        "status": "success",
        "result": {
            "origin": NODES_FULL_DATA[start_id].get("name"),
            "destination": NODES_FULL_DATA[target_id].get("name"),
            "total_distance_meters": round(cost, 2),
            "node_count": len(path),
            "path_nodes": path,
            "path_edges": path_edges,
        },
    })


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory(".", filename)


@app.route("/api/edge_list")
def get_edge_list():
    edge_list_path = os.path.join(PROJECT_ROOT, "data", "processed", "outputs", "edge_list.json")
    try:
        with open(edge_list_path, "r", encoding="utf-8") as file:
            return jsonify(json.load(file))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/station_list")
def get_station_list():
    station_dict_path = os.path.join(PROJECT_ROOT, "data", "processed", "outputs", "station_dict.json")
    try:
        with open(station_dict_path, "r", encoding="utf-8") as file:
            stations = json.load(file)

        station_list = []
        for station_id, station_data in stations.items():
            station_list.append(
                {
                    "id": station_id,
                    "name": station_data.get("name", ""),
                    "name_en": station_data.get("name_en", ""),
                    "colour": station_data.get("colour", ""),
                    "line_id": station_data.get("line_id", ""),
                    "geometry": station_data.get("geometry", []),
                    "stops": station_data.get("stops", []),
                }
            )
        return jsonify(station_list)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/api/stations")
def proxy_stations():
    try:
        return _proxy_json("/stations")
    except HTTPError as exc:
        return jsonify({"error": f"Root API returned {exc.code}: {exc.reason}"}), exc.code
    except URLError as exc:
        try:
            return jsonify(_load_station_fallback())
        except Exception:
            return jsonify({"error": f"Cannot reach root API: {exc.reason}"}), 502
    except Exception as exc:
        try:
            return jsonify(_load_station_fallback())
        except Exception:
            return jsonify({"error": str(exc)}), 500


@app.route("/api/find-path", methods=["POST"])
def proxy_find_path():
    payload = request.get_json(silent=True) or {}

    try:
        return _proxy_json("/find-path", method="POST", body=request.get_data())
    except HTTPError as exc:
        try:
            payload = exc.read().decode("utf-8")
            return Response(payload, status=exc.code, content_type="application/json")
        except Exception:
            return jsonify({"error": f"Root API returned {exc.code}: {exc.reason}"}), exc.code
    except URLError as exc:
        return _find_path_local(payload)
    except Exception as exc:
        return _find_path_local(payload)


if __name__ == "__main__":
    print("Moscow Metro Pathfinder - Web Frontend")
    print("=" * 50)
    print("Frontend Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)
