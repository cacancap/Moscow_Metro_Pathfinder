# 🚇 Dự án: Moscow Metro Pathfinder

## 1. Tổng quan dự án (Project Overview)
- **Mục tiêu:** Xây dựng hệ thống tìm đường (routing) và trực quan hóa bản đồ tương tác cho mạng lưới Tàu điện ngầm Moscow.
- **Backend:** Python 3.13, FastAPI (unified `server.py`) — xử lý dữ liệu đồ thị từ SQLite, cung cấp REST API pathfinding (A*, Dijkstra, BFS) và dữ liệu bản đồ.
- **Frontend:** HTML/CSS/JS thuần, Leaflet.js 1.9.4 — giao diện bản đồ tương tác, tìm đường, mô phỏng sự cố mạng lưới.

## 2. Cấu trúc thư mục cốt lõi (Directory Structure)

```
Moscow_Metro_Pathfinder/
├── algorithm/          # Thuật toán tìm đường: A* (astar.py), Dijkstra, BFS, heuristics
├── data/
│   ├── processed/outputs/  # JSON xuất ra: edge_list, station_dict, adjacency_list…
│   └── raw/            # Dữ liệu GeoJSON gốc từ OSM
├── docs/standards/     # Tài liệu kỹ thuật: api_contracts, data_contracts, AGENTS
├── web/                # Toàn bộ frontend tĩnh
│   ├── index.html      # Trang đăng nhập
│   ├── map.html        # Bản đồ chính (user + admin)
│   ├── admin.html      # Bảng điều khiển admin
│   ├── script.js       # Logic bản đồ, routing, bomb, edge layer
│   ├── admin.js        # Logic quản lý đóng ga/cạnh
│   ├── auth.js         # Auth, localStorage helpers, API endpoints, shared utils
│   ├── map_click.js    # Click tìm ga gần nhất
│   └── style.css       # Design system (Moscow red #c8102e, Manrope/Space Grotesk)
├── server.py           # Entry point FastAPI duy nhất (port 5000)
├── run.py              # Script khởi động (gọi uvicorn server:app)
├── moscow_metro.db     # SQLite — nguồn dữ liệu runtime
└── requirements.txt
```

## 3. Ngăn xếp công nghệ (Tech Stack)

| Tầng | Công nghệ |
|---|---|
| Backend | Python 3.13, FastAPI, uvicorn, SQLite (qua sqlite3) |
| Frontend | HTML5, CSS3, JavaScript (ES6+) thuần |
| Bản đồ | Leaflet.js 1.9.4 (tile: OpenStreetMap) |
| Font | Space Grotesk (headings), Manrope (body) |
| State | localStorage (blockedNodes, blockedEdges, bombs, routeHistory) |

## 4. Kiến trúc Runtime

```
python run.py
  └─> uvicorn server:app --host 127.0.0.1 --port 5000
        ├── GET  /                    → redirect /map.html
        ├── GET  /api/stations        → danh sách stop nodes (bỏ fake/)
        ├── GET  /api/station_list    → catalog ga với metadata đầy đủ
        ├── GET  /api/edge_list       → danh sách cạnh đồ thị
        ├── GET  /api/network-summary → thống kê mạng lưới
        ├── GET  /api/nearest-station → ga gần tọa độ nhất
        ├── POST /api/find-path       → tìm đường (A*/Dijkstra/BFS)
        ├── POST /api/admin/bomb-closure → tính nodes/edges bị ảnh hưởng bởi vụ nổ
        ├── /data/...                 → file dữ liệu tĩnh
        └── /...                     → file tĩnh từ web/
```

## 5. Quy ước Code (Coding Standards)

### Chung:
- Suy nghĩ theo từng bước (think step-by-step) trước khi viết code.
- Ưu tiên hiệu suất và tối ưu bộ nhớ khi xử lý JSON đồ thị lớn.
- Comment bằng tiếng Việt cho logic phức tạp; tên biến/hàm bằng tiếng Anh.

### Frontend (`web/script.js`):
- **Tọa độ:** dữ liệu lưu `[lon, lat]` (GeoJSON), Leaflet dùng `[lat, lon]` — luôn đảo khi vẽ.
- **State chính:** object `state` trong `script.js` — không tạo global lẻ mới.
- **Blocked config:** đọc qua `getEffectiveBlockedConfig()` (gộp manual + bomb); ghi manual qua `saveBlockedConfig()`.
- **Edge layer:** `state.edgeLayer` (LayerGroup), toggle bằng `toggleEdgeLayer()`, re-render qua `refreshEdgeVisuals()`.
- **Cache bust:** khi thêm hàm mới vào JS, tăng `?v=N` trong `<script src>` của map.html để tránh browser cache cũ.

### Backend (`server.py`):
- Dữ liệu load từ SQLite vào `DB_CACHE` khi startup (lifespan), không đọc file JSON runtime.
- Pathfinding: gọi qua `algorithm/astar.py`, `algorithm/dijkstra.py`, `algorithm/bfs.py`.

## 6. Tính năng Frontend hiện tại

| Tính năng | File | Mô tả |
|---|---|---|
| Bản đồ ga | `script.js` | Marker màu theo tuyến, click mở panel chi tiết |
| Tìm đường | `script.js` | Dropdown ga đi/đến, thuật toán A*/Dijkstra/BFS; đường đi render màu **magenta `#e91e63`** cố định trên `routePane` (z-index 450) — luôn đè lên edge layer |
| Edge layer | `script.js` | **Bật mặc định khi load.** Nút "🛤 Đường ray" toggle ẩn/hiện; cạnh bị đóng hiển thị nét đứt đỏ |
| Click cạnh trên map | `script.js` | Click thẳng vào đường ray trên bản đồ → mở panel cạnh. Dùng `onMapEdgeClick()` (map-level hit-test pixel, tolerance 8px). Station click được ưu tiên nhờ flag `state.stationClicked` |
| Panel chi tiết cạnh | `script.js` | Click vào cạnh → xem edge_id, tuyến, ga đầu/cuối, khoảng cách, trạng thái; admin có nút đóng/mở (disabled nếu bị chặn bởi bom) |
| Đóng/mở ga & cạnh | `script.js` | Admin: nút toggle trực tiếp trên panel; **không thể mở thủ công ga/cạnh đang bị chặn bởi bom** |
| Chip closure clickable | `script.js` | Ga bị đóng: click chip → `focusStation()` + mở panel. Cạnh bị đóng: click chip → `focusEdge()` (fly to + highlight 2s) + mở panel |
| Bomb system | `script.js` | Admin: click tọa độ → bán kính → kích nổ; block cả nodes lẫn edges trong vùng |
| Dropdown ga đích | `script.js` | Hiển thị **tất cả ga không bị chặn** (kể cả không kết nối được); cảnh báo "không có đường đi" khi ga đích bị cô lập |
| Admin dashboard | `admin.js` | Tìm và chọn ga/cạnh để đóng, lưu vào localStorage |
| Click tìm ga gần nhất | `map_click.js` | Click bản đồ → gọi `/api/nearest-station` → hiện popup |

## 7. Lệnh thường dùng (Common Commands)

```bash
# Khởi động toàn bộ ứng dụng (khuyến nghị)
python run.py

# Hoặc chạy trực tiếp
uvicorn server:app --host 127.0.0.1 --port 5000 --reload
```

- **Web App:** http://127.0.0.1:5000
- **API Docs (Swagger):** http://127.0.0.1:5000/docs
- **Tài khoản admin:** `admin` / `admin12321`
- **Tài khoản user:** bất kỳ username/password

## 8. Lưu ý quan trọng cho AI Assistant

- Runtime duy nhất là `server.py` (FastAPI, port 5000) — **không còn** `api.py` (port 8000) + `web/app.py` (Flask) như tài liệu cũ.
- Mọi thay đổi JS quan trọng cần tăng version `?v=N` trong script src của `map.html` để tránh browser cache. Script hiện tại: `script.js?v=9`.
- `getEffectiveBlockedConfig()` trong `auth.js` gộp blockedNodes/Edges từ cả manual config lẫn bomb data — luôn dùng hàm này thay vì đọc localStorage trực tiếp.
- `state.edgeById` là Map từ `edge_id` → edge object, dùng để tra cứu nhanh khi render edge layer.
- **Edge layer bật mặc định** — `renderEdgePolylines()` được gọi tự động trong `loadAppData()` sau khi data load xong.
- **Route path**: `renderPath()` vẽ một polyline duy nhất màu `#e91e63` (magenta), weight 9, đặt trong `routePane` (z-index 450). Pane này được tạo trong `buildMap()` và nằm trên overlayPane (400 — nơi edge layer render) nhưng dưới markerPane (600 — nơi station marker render).
- **Edge click trên map**: `onMapEdgeClick()` đăng ký trên `state.map.on("click")`. Tính khoảng cách pixel từ điểm click đến từng đoạn thẳng của cạnh (`ptSegDistPx`); mở panel nếu ≤ 8px. Station click được ưu tiên nhờ `state.stationClicked` flag (set trong `marker.on("click")`, reset bằng `setTimeout(..., 0)`).
- **Bomb-blocked bảo vệ**: `openStationPanel()` và `openEdgePanel()` kiểm tra nếu item bị bomb-blocked (có trong `getEffectiveBlockedConfig()` nhưng không có trong `getBlockedConfig()`) thì disable nút đóng/mở và đặt tooltip. `toggleStationBlockFromPanel()` và `toggleEdgeBlockFromPanel()` cũng có guard tương tự để tránh ghi sai vào manual config.
- **`focusEdge(edge)`**: Fly map đến bounding box của cạnh (`fitBounds`), highlight polyline cam 2 giây nếu edge layer đang hiển thị. Gọi từ chip click trong `renderClosureSummary()`.
- **Dropdown ga đích hiển thị tất cả ga** — `populateStationSelects()` không lọc theo reachability; `updateReachabilityWarning()` hiển thị cảnh báo khi ga đích bị cô lập.
- `updateReachabilityWarning(startId, endId)` — kiểm tra `state.reachableEndIds` và toggle `#noRouteWarning`; gọi trong `populateStationSelects()` và `updateSelectionSummary()`.
