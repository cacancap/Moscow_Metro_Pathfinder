# Data Contracts (Runtime)

This document defines the runtime data contracts used by the main application flow:

- `python run.py`
- backend: `api.py`
- frontend: `web/app.py` + `web/script.js` + `web/admin.js`

## 1) File Overview

### `data/processed/outputs/stop_dict_id.json`

- Type: `hashmap` keyed by stop `id`.
- Purpose: store stop metadata for direct lookup by stop ID.
- Typical usage: build/inspection scripts and data debugging.

Example shape:

```json
{
  "242546357": {
    "id": "242546357",
    "name": "Some Stop",
    "name_en": "Some Stop EN",
    "lat": 55.75,
    "lon": 37.61
  }
}
```

---

### `data/processed/outputs/stop_dict_coord.json`

- Type: `hashmap` keyed by coordinate-derived key.
- Purpose: store stop metadata for coordinate-based lookup.
- Runtime importance: used by `api.py` startup and Flask local fallback to build `nodes_full_data`.

Example shape:

```json
{
  "37.6583103,55.7581156": {
    "id": "242546357",
    "name": "Some Stop",
    "lat": 55.7581156,
    "lon": 37.6583103
  }
}
```

---

### `data/processed/outputs/station_dict.json`

- Type: `hashmap` keyed by station ID.
- Purpose: store station-level metadata.
- Important relation: each station contains references to its stops (`stops` list).
- Runtime importance: used by Flask endpoint `/api/station_list` for UI station catalog.

Example shape:

```json
{
  "station_001": {
    "name": "Курская",
    "name_en": "Kurskaya",
    "line_id": ["3", "5"],
    "colour": "blue",
    "geometry": [[37.6583, 55.7581]],
    "stops": ["242546357", "242546358"]
  }
}
```

---

### `data/processed/outputs/edge_list.json`

- Type: `list` of edge objects.
- Purpose: represent graph edges connecting nodes/stops.
- Runtime importance: used by Flask endpoint `/api/edge_list`; frontend uses this to build adjacency for UI rendering and route details.

Example shape:

```json
[
  {
    "edge_id": "e_201",
    "source_id": "242546357",
    "dest_id": "fake/172",
    "weight": 101.21,
    "edge_type": "subway",
    "line_id": "3",
    "colour": "blue",
    "geometry": [[37.6583, 55.7581], [37.6569, 55.7576]]
  }
]
```

---

### `data/processed/outputs/adjacency_list.json`

- Type: adjacency map (nested hashmap).
- Purpose: primary graph structure for fast edge metadata lookup by `(source_id, dest_id)`.
- Runtime importance: **most critical file for pathfinding APIs**.
  - `api.py` loads this at startup and uses it with A*.
  - `web/app.py` local fallback also uses this file.

Example shape:

```json
{
  "242546357": {
    "fake/172": {
      "edge_id": "e_201",
      "weight": 101.21,
      "edge_type": "subway",
      "line_id": "3"
    }
  }
}
```

## 2) Domain Notes

### Transfer edges

- Edges with transfer semantics represent walking connections between lines/stations.
- Typical marker: `edge_type = "transfer"` (or equivalent transfer/walk line markers such as `line_id = "walk"` depending on source pipeline).
- These edges are valid route options and must be handled by pathfinding unless blocked by runtime constraints.

### Fake nodes

- Node IDs with prefix `fake/` are synthetic connector nodes.
- Purpose: maintain graph connectivity between ways/segments that need explicit linking.
- They are part of routing internals and may appear in computed paths.

## 3) Runtime Contract in API Layer

Main API flow (`api.py`):

- Startup:
  - Load `stop_dict_coord.json` into `nodes_full_data` (`{node_id: metadata}`).
  - Load `adjacency_list.json` into `graph_data`.
- Pathfinding endpoint:
  - Input: `start_id`, `target_id`, `blocked_edges`, `blocked_nodes`.
  - Engine: `algorithm.astar.a_star_search(...)`.
  - Output includes `path_nodes` and derived `path_edges`.

Flask layer (`web/app.py`):

- Provides UI-facing endpoints:
  - `/api/station_list` from `station_dict.json`
  - `/api/edge_list` from `edge_list.json`
  - `/api/stations` and `/api/find-path` proxied to root FastAPI with local fallback using runtime graph data.

## 4) Validation Recommendations

When updating data pipeline, validate at least:

- Every `source_id`/`dest_id` in `edge_list.json` exists in runtime node set.
- `adjacency_list.json` and `edge_list.json` are consistent for edge IDs and weights.
- `station_dict.json.stops[]` references valid stop IDs.
- Transfer edges and fake nodes remain connected to avoid route fragmentation.
