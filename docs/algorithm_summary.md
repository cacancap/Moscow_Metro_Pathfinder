# Tóm tắt — Nhóm Thuật Toán

> Dành cho nhóm Web để nắm nhanh những gì đã xây dựng và cách tích hợp.

---

## 1. Những gì đã làm

### `algorithm/graph.py`
| Hàm | Tác dụng |
|---|---|
| `load_graph()` | Đọc `adjacency_list.json`, trả về `(graph, nodes)` |
| `haversine(nodes, a, b)` | Tính km đường chim bay giữa 2 node — dùng làm heuristic A\* |
| `filter_graph(graph, exclude_edges)` | Xóa các cạnh bị cấm, trả về đồ thị mới để chạy thuật toán |

### `algorithm/pathfinder.py`
| Hàm | Tác dụng |
|---|---|
| `find_path(graph, nodes, start_id, goal_id, algorithm)` | Hàm chính — chạy BFS / Dijkstra / A\* và trả kết quả |

**3 thuật toán:**
- **BFS** — ít ga nhất (không tính khoảng cách)
- **Dijkstra** — ngắn nhất theo km
- **A\*** — ngắn nhất theo km, nhanh hơn Dijkstra nhờ heuristic *(mặc định)*

### `server.py`
FastAPI server phục vụ cả UI lẫn API. Chạy bằng:
```bash
python -m uvicorn server:app --reload --port 5000
```
Mở trình duyệt: `http://127.0.0.1:5000`

---

## 2. API endpoints

### `GET /api/lines`
Trả về danh sách 20 tuyến để UI hiển thị checkbox cấm tuyến.

```json
[
  { "name": "Сокольническая линия", "colour": "red"   },
  { "name": "Арбатско-Покровская линия", "colour": "blue"  },
  { "name": "Кольцевая линия", "colour": "brown" }
]
```

---

### `GET /api/path`
Tìm đường giữa 2 điểm click trên bản đồ.

**Tham số:**

| Tham số | Bắt buộc | Mô tả |
|---|---|---|
| `s_lat`, `s_lng` | Có | Tọa độ điểm xuất phát |
| `e_lat`, `e_lng` | Có | Tọa độ điểm đích |
| `algorithm` | Không | `astar` *(mặc định)* / `dijkstra` / `bfs` |
| `exclude_lines` | Không | Tên tuyến bị cấm, **lặp lại** để cấm nhiều tuyến |

**Ví dụ — không cấm tuyến:**
```
GET /api/path?s_lat=55.758&s_lng=37.658&e_lat=55.730&e_lng=37.446
```

**Ví dụ — cấm 2 tuyến:**
```
GET /api/path?s_lat=55.758&s_lng=37.658&e_lat=55.730&e_lng=37.446
             &exclude_lines=Сокольническая линия
             &exclude_lines=Кольцевая линия
```

**Response thành công (200):**
```json
{
  "path":           [[55.758, 37.658], [55.757, 37.655], "..."],
  "distance_km":    16.915,
  "num_stations":   119,
  "elapsed_ms":     0.8,
  "start_id":       "node_auto_1",
  "goal_id":        "node_auto_3",
  "excluded_lines": ["Сокольническая линия"]
}
```
> `path` là mảng `[lat, lon]` — dùng **trực tiếp** cho `L.polyline()` của Leaflet.

**Response thất bại (404):**
```json
{ "detail": "Không tìm được đường đi. Có thể các tuyến bị cấm đã chặn toàn bộ lộ trình." }
```

---

## 3. Cách nhóm Web tích hợp

### Bước 1 — Load danh sách tuyến khi khởi động
```js
async function loadLines() {
    const res = await fetch('/api/lines');
    const lines = await res.json();
    // Render checkbox cho từng tuyến
    lines.forEach(line => {
        // line.name   -> tên tuyến (dùng làm value của checkbox)
        // line.colour -> màu sắc   (dùng để tô màu checkbox)
    });
}
```

### Bước 2 — Gọi API khi user chọn 2 điểm và bấm tìm đường
```js
async function findPath(sLat, sLng, eLat, eLng) {
    // Lấy danh sách tuyến bị tích checkbox
    const banned = [...document.querySelectorAll('.line-checkbox:checked')]
                   .map(el => el.value);

    const params = new URLSearchParams({
        s_lat: sLat, s_lng: sLng,
        e_lat: eLat, e_lng: eLng,
        algorithm: 'astar'
    });
    banned.forEach(line => params.append('exclude_lines', line));

    const res = await fetch(`/api/path?${params}`);

    if (!res.ok) {
        const err = await res.json();
        alert(err.detail);  // "Không tìm được đường đi..."
        return;
    }

    const data = await res.json();

    // Vẽ đường lên bản đồ Leaflet
    L.polyline(data.path, { color: 'red', weight: 4 }).addTo(map);

    // Hiển thị thông tin
    console.log(`${data.distance_km} km | ${data.num_stations} ga | ${data.elapsed_ms} ms`);
}
```

### Bước 3 — Bỏ comment trong `draw_path.js`
Xóa đoạn demo đường thẳng (dòng 48–55) và bỏ comment đoạn `PHẦN THỰC TẾ` (dòng 60–67), thay URL thành `/api/path`.

---

## 4. Kết quả test thực tế

| Kịch bản | Kết quả |
|---|---|
| Không cấm | 16.9 km — đường ngắn nhất |
| Cấm tuyến không liên quan | 16.9 km — không ảnh hưởng |
| Cấm tuyến chính | 28.8 km — tìm đường vòng thay thế |
| Cấm 2–3 tuyến | 30–33 km — vẫn tìm được |
| Cấm 10+ tuyến lớn | **404** — không tìm được đường |

---

## 5. Lưu ý

- Node loại `hub` trong `path` là điểm chuyển tuyến ảo — **không hiển thị tên** nhưng vẫn dùng tọa độ để vẽ đường.
- `path` trả về `[lat, lon]` — Leaflet dùng đúng thứ tự này cho `L.polyline()`.
- `load_graph()` chỉ gọi **một lần** khi server khởi động, không gọi lại mỗi request.