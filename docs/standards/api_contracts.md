# API Contracts — Main Runtime

This document describes the API contract for the current main runtime flow:

1. Run `python run.py`
2. `run.py` starts:
   - Root FastAPI service: `api.py` at `127.0.0.1:8000`
   - Flask web service: `web/app.py` at `127.0.0.1:5000`

The browser calls APIs through Flask (`/api/...`). Flask proxies to FastAPI and provides local fallback behavior for selected endpoints.

**Note:** `api.py` returns Vietnamese `detail` strings for some errors (as implemented in code). Shapes below are stable; wording matches the server.

---

## 1) Root API (FastAPI — port 8000)

### 1.1 `GET /stations`

Purpose:

- Return real stations for start/end dropdown selection.
- Exclude nodes with the `fake/` prefix.

Response `200`:

```json
[
  {
    "id": "242546357",
    "name": "Курская"
  }
]
```

Errors: FastAPI defaults unless a handler raises explicitly.

---

### 1.2 `POST /find-path`

Purpose:

- Find the shortest route with A* using `adjacency_list.json`.
- Support dynamic blocking via `blocked_edges` and `blocked_nodes`.

Request body:

```json
{
  "start_id": "242546357",
  "target_id": "296944266",
  "blocked_edges": ["e_201"],
  "blocked_nodes": ["fake/172"]
}
```

Rules:

- `start_id`, `target_id`: required, must exist in `nodes_full_data`.
- `blocked_edges`, `blocked_nodes`: optional, default to `[]`.

Response `200`:

```json
{
  "status": "success",
  "result": {
    "origin": "Курская",
    "destination": "Китай-город",
    "total_distance_meters": 1234.56,
    "node_count": 7,
    "path_nodes": ["242546357", "fake/172", "296944266"],
    "path_edges": ["e_201", "e_1242"]
  }
}
```

Response `400` (examples from `api.py`):

```json
{
  "detail": "Ga đi (ID: xxx) không tồn tại."
}
```

or

```json
{
  "detail": "Ga đến (ID: yyy) không tồn tại."
}
```

Response `404`:

```json
{
  "detail": "Không tìm thấy lộ trình. Có thể các ga mục tiêu đã bị đóng cửa hoặc đường đi bị phong tỏa."
}
```

---

## 2) Web API (Flask — port 5000, browser-facing)

These are the endpoints called by frontend JavaScript.

### 2.1 `GET /api/station_list`

Data source:

- Read directly from `data/processed/outputs/station_dict.json`.

Purpose:

- Return a station catalog with metadata for map rendering and search.

Response `200`:

```json
[
  {
    "id": "station_001",
    "name": "Курская",
    "name_en": "Kurskaya",
    "colour": "blue",
    "line_id": ["3", "5"],
    "geometry": [[37.6583, 55.7581]],
    "stops": ["242546357", "242546358"]
  }
]
```

### 2.2 `GET /api/edge_list`

Data source:

- Read directly from `data/processed/outputs/edge_list.json`.

Purpose:

- Return edge data so frontend can build adjacency and show route details.

Response `200`:

- Array of edge objects, preserving the source data schema.

### 2.3 `GET /api/stations`

Purpose:

- Browser API for route-stop station list retrieval.

Behavior:

- Proxy to FastAPI `GET /stations`.
- If FastAPI is unreachable: local fallback using loaded data from
  `stop_dict_coord.json` and excluding `fake/` nodes.

Response:

- Same schema as root API `GET /stations`.

### 2.4 `POST /api/find-path`

Purpose:

- Browser API for route search.

Behavior:

- Proxy to FastAPI `POST /find-path` with unchanged request body.
- If FastAPI is unreachable or proxy fails: local fallback via `algorithm.astar.a_star_search`.

Request/response:

- Uses the same contract as root API `POST /find-path` when proxied successfully.
- Local fallback returns the same JSON shape as `api.py` success path; errors use `detail` with the same Vietnamese strings as `api.py` / Flask local handler.

---

## 3) API Data Dependencies

Current runtime API depends on:

- `data/processed/outputs/stop_dict_coord.json`
- `data/processed/outputs/adjacency_list.json`
- `data/processed/outputs/station_dict.json`
- `data/processed/outputs/edge_list.json`

The main runtime does not use the legacy `Khanh` branch contracts.

---

## 4) Team Notes

- `fake/...` is a valid routing node and may appear in `path_nodes`.
- Frontend rendering relies on station catalog (`station_dict`) and route stations (`/api/stations`), not on `algorithm/graph.py` or `algorithm/pathfinder.py`.
- If output data schema changes, update all of the following together:
  - `api.py`
  - `web/app.py`
  - `web/script.js` and `web/admin.js`
