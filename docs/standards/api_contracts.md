# API Contracts — Runtime (server.py)

Runtime duy nhất: `python run.py` → `uvicorn server:app --host 127.0.0.1 --port 5000`.

Tất cả endpoints đều trên **port 5000**. Không còn kiến trúc Flask + FastAPI riêng.

---

## GET /api/stations

Trả về danh sách stop nodes dùng cho dropdown chọn ga (loại bỏ `fake/` prefix).

**Response 200:**
```json
[
  { "id": "242546357", "name": "Курская" }
]
```

---

## GET /api/station_list

Trả về catalog ga đầy đủ để render bản đồ và tìm kiếm.

**Response 200:**
```json
[
  {
    "id": "station_001",
    "name": "Курская",
    "name_en": "Kurskaya",
    "colour": "blue",
    "line_id": "3",
    "geometry": [37.6583, 55.7581],
    "stops": ["242546357", "242546358"]
  }
]
```

> `geometry` là `[lon, lat]` (GeoJSON). Leaflet cần đảo thành `[lat, lon]`.

---

## GET /api/edge_list

Trả về toàn bộ cạnh đồ thị để frontend build adjacency, render edge layer.

**Response 200:**
```json
[
  {
    "edge_id": "e_201",
    "source_id": "242546357",
    "dest_id": "fake/172",
    "weight": 101.21,
    "line_id": "3",
    "edge_type": "subway",
    "colour": "blue",
    "geometry": [[37.6583, 55.7581], [37.6569, 55.7576]]
  }
]
```

> `geometry` mỗi điểm là `[lon, lat]`.

---

## GET /api/network-summary

Trả về thống kê mạng lưới để hiển thị trong panel.

**Response 200:**
```json
{
  "data_source": "data/processed/outputs",
  "station_nodes": 240,
  "station_groups": 198,
  "edges": 512,
  "lines": { "1": 48, "2": 52 },
  "ways": 310
}
```

---

## GET /api/nearest-station?lat=55.75&lon=37.61

Tìm ga gần tọa độ nhất (dùng cho click bản đồ → tìm ga gần nhất).

**Response 200:**
```json
{
  "id": "station_001",
  "name": "Курская",
  "name_en": "Kurskaya",
  "distance_meters": 87.4,
  "lat": 55.7581,
  "lon": 37.6583
}
```

**Response 404:** `{ "error": "No station found" }`

---

## POST /api/find-path

Tìm đường ngắn nhất hỗ trợ chặn động ga và cạnh.

**Request body:**
```json
{
  "start_id": "242546357",
  "target_id": "296944266",
  "algorithm": "astar",
  "blocked_edges": ["e_201"],
  "blocked_nodes": ["fake/172"]
}
```

- `algorithm`: `"astar"` (mặc định) | `"dijkstra"` | `"bfs"`
- `blocked_edges`, `blocked_nodes`: optional, default `[]`

**Response 200:**
```json
{
  "status": "success",
  "result": {
    "origin": "Курская",
    "destination": "Китай-город",
    "total_distance_meters": 1234.56,
    "node_count": 7,
    "elapsed_ms": 2.1,
    "path_nodes": ["242546357", "fake/172", "296944266"],
    "path_edges": ["e_201", "e_1242"]
  }
}
```

**Response 400:** `{ "detail": "Ga đi (ID: xxx) không tồn tại." }`

**Response 404:** `{ "detail": "Không tìm thấy lộ trình. Có thể ga đã đóng hoặc các đoạn nối đang bị chặn." }`

---

## POST /api/admin/bomb-closure

Tính toán tập nodes và edges bị ảnh hưởng bởi vụ nổ (dùng bởi bomb system phía frontend để đồng bộ với server).

**Request body:**
```json
{
  "lat": 55.751,
  "lon": 37.618,
  "radius_meters": 1000.0
}
```

**Response 200:**
```json
{
  "blocked_nodes": ["242546357", "296944266"],
  "blocked_edges": ["e_201", "e_202"],
  "blocked_node_count": 2,
  "blocked_edge_count": 2
}
```

---

## GET /api/health

Kiểm tra server và dữ liệu đã load.

**Response 200:** `{ "status": "ok", "station_nodes": 240, "edges": 512, ... }`

**Response 500:** `{ "status": "error", "error": "..." }`

---

## Ghi chú triển khai

- **Dữ liệu:** load từ `moscow_metro.db` (SQLite) vào `DB_CACHE` khi startup, không đọc JSON file runtime.
- **Blocking:** `blocked_nodes` / `blocked_edges` truyền từ frontend (localStorage) qua request body — server **không lưu trạng thái**, mỗi request tự chứa đủ thông tin.
- **Frontend state:** `getEffectiveBlockedConfig()` trong `auth.js` gộp manual config + bomb data từ localStorage.
- **Fake nodes:** `fake/...` là connector node tổng hợp — hợp lệ trong `path_nodes`, không xuất hiện trong `/api/stations`.
