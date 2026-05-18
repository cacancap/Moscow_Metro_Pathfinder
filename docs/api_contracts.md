# API Contracts — Nhóm Thuật Toán ↔ Nhóm Web

## 1. Import

```python
from algorithm.graph import load_graph
from algorithm.pathfinder import find_path
```

Gọi `load_graph()` **một lần duy nhất** khi khởi động app, lưu kết quả vào biến dùng chung:

```python
graph, nodes = load_graph()
```

---

## 2. Hàm chính: `find_path()`

```python
def find_path(graph, nodes, start_id, goal_id, algorithm="astar")
```

### Tham số

| Tham số | Kiểu | Mô tả |
|---|---|---|
| `graph` | `dict` | Kết quả từ `load_graph()` |
| `nodes` | `dict` | Kết quả từ `load_graph()` |
| `start_id` | `str` | Node ID ga xuất phát (vd: `"node_auto_1"`) |
| `goal_id` | `str` | Node ID ga đích |
| `algorithm` | `str` | `"astar"` *(mặc định)*, `"dijkstra"`, `"bfs"` |

### Giá trị trả về

```python
{
    "path":         ["node_auto_1", "node_auto_0", ..., "node_auto_7"],  # danh sách node ID theo thứ tự
    "distance_km":  21.5390,   # tổng km (float, làm tròn 4 chữ số)
    "num_stations": 162,       # số node trong path (bao gồm điểm đầu và cuối)
    "elapsed_ms":   4.213,     # thời gian chạy thuật toán (ms)
}
```

Trả về `None` nếu **không tìm được đường** (đồ thị mất liên thông hoặc ID không tồn tại).

---

## 3. Lấy tên và tọa độ ga — `station_metadata.json`

Nhóm Web tự load file này để hiển thị tên và vẽ marker:

```python
import json

with open("data/processed/Khanh/04_final_output/station_metadata.json", encoding="utf-8") as f:
    meta = json.load(f)
```

Cấu trúc mỗi entry:

```python
meta["node_auto_1"] = {
    "name_en": "Kurskaya",
    "name_ru": "Курская",
    "node_type": "station",   # "station" | "hub"
    "lines": ["line_id_1", ...],
    # tọa độ hiển thị lấy từ nodes dict của load_graph()
}
```

Tọa độ `[lon, lat]` lấy từ `nodes` (kết quả `load_graph()`):

```python
graph, nodes = load_graph()
lon, lat = nodes["node_auto_1"]   # [37.658, 55.758]
```

---

## 4. Ví dụ tích hợp hoàn chỉnh

```python
from algorithm.graph import load_graph
from algorithm.pathfinder import find_path

# Khởi động (chạy 1 lần)
graph, nodes = load_graph()

# Khi người dùng bấm "Tìm đường"
result = find_path(graph, nodes, start_id="node_auto_1", goal_id="node_auto_7")

if result is None:
    st.error("Không tìm được đường đi.")
else:
    st.metric("Khoảng cách", f"{result['distance_km']} km")
    st.metric("Số ga",       result["num_stations"])
    st.metric("Thời gian tính", f"{result['elapsed_ms']} ms")

    # Vẽ path lên bản đồ Folium
    coords = [[nodes[n][1], nodes[n][0]] for n in result["path"]]  # [lat, lon]
    folium.PolyLine(coords, color="red", weight=4).add_to(m)
```

---

## 5. So sánh 3 thuật toán

| Thuật toán | Ưu tiên | Tốc độ | Dùng khi |
|---|---|---|---|
| `"astar"` | Ngắn nhất (km) | Nhanh nhất | Mặc định — luôn dùng cái này |
| `"dijkstra"` | Ngắn nhất (km) | Chậm hơn A\* | Dự phòng / so sánh |
| `"bfs"` | Ít ga nhất | Nhanh | Khi người dùng muốn ít điểm dừng |

---

## 6. Lưu ý

- `start_id` và `goal_id` phải là key hợp lệ trong `nodes`. Nhóm Web tự validate trước khi gọi.
- Node loại `hub` (Virtual Hub) sẽ xuất hiện trong `path` — đây là điểm chuyển tuyến ảo, **không hiển thị tên** cho người dùng nhưng **vẫn dùng tọa độ** để vẽ đường.
- Đơn vị tọa độ: `[lon, lat]` — Folium dùng `[lat, lon]`, cần đảo khi vẽ (xem ví dụ mục 4).