# CLAUDE.md — Moscow Metro Pathfinder

## Tổng quan dự án

Hệ thống tìm đường tàu điện ngầm Moscow sử dụng thuật toán AI (A\*, Dijkstra, BFS) trên dữ liệu OSM thực tế. Giao diện web bằng Streamlit + Folium.

**Nhóm 14 — Nhập môn AI 2025.2**

---

## Vai trò của tôi: Nhóm Thuật toán (Algorithm)

Tôi chịu trách nhiệm phần lõi AI: đọc đồ thị từ dữ liệu đã xử lý, cài đặt thuật toán tìm đường, và xuất kết quả cho nhóm Web tích hợp.

---

## Dữ liệu đầu vào (do nhóm Dữ liệu cung cấp — ĐÃ HOÀN THÀNH)

File chính nằm tại `data/processed/Khanh/04_final_output/`:

### `adjacency_list.json`
Dùng trực tiếp cho A\* và Dijkstra.
```json
{
  "nodes": { "node_id": [lon, lat] },
  "graph": { "source_id": { "target_id": weight_km } }
}
```
- Trọng số `weight` đơn vị **kilomet (km)**.
- `nodes` dùng để tính heuristic khoảng cách chim bay (Haversine).
- Tra cứu láng giềng O(1).

### `station_metadata.json`
Dùng cho giao diện: tên tiếng Nga/Anh, tọa độ hiển thị, loại node, danh sách tuyến.

### Đặc điểm đồ thị
- Node loại `hub` là **Virtual Hub** — điểm trung chuyển ảo giữa các tuyến, có cạnh `transfer` với trọng số phạt.
- Đồ thị **liên thông 100%** (đã xác minh bởi `verify_graph.py`).
- 37 Virtual Hubs xử lý chuyển tuyến.

---

## Cấu trúc thư mục liên quan

```
algorithm/
  graph.py        # Nạp adjacency_list.json, xây Graph object
  pathfinder.py   # BFS, Dijkstra, A* — hàm find_path()
  __init__.py

data/processed/Khanh/04_final_output/
  adjacency_list.json
  station_metadata.json

docs/
  api_contracts.md   # Giao kèo interface với nhóm Web
```

---

## Thuật toán cần cài đặt

### Hàm heuristic h(n)
Khoảng cách chim bay (Haversine) từ node hiện tại đến đích — đơn vị km.
- Admissible: không bao giờ overestimate → A\* đảm bảo tối ưu.
- Consistent: thỏa bất đẳng thức tam giác → dùng được với graph-search (closed set).

### f(n) = g(n) + h(n)
- `g(n)`: chi phí thực tế từ start đến n (km đã đi).
- `h(n)`: Haversine từ n đến goal (km ước tính).

### Thứ tự cài đặt
1. **BFS** — tìm đường ít ga nhất (không dùng weight).
2. **Dijkstra** — tìm đường ngắn nhất theo km.
3. **A\*** — mục tiêu chính, kết hợp Dijkstra + Haversine heuristic.

### Path reconstruction
Mỗi node trong quá trình duyệt lưu `came_from`. Khi chạm đích, trace ngược về start rồi reverse.

---

## API contract với nhóm Web

Hàm chính mà nhóm Web sẽ import:

```python
def find_path(graph, nodes, start_id, goal_id, algorithm="astar"):
    # Returns:
    # {
    #   "path": [node_id, ...],      # danh sách ga theo thứ tự
    #   "distance_km": float,        # tổng km
    #   "num_stations": int,
    #   "elapsed_ms": float
    # }
```

---

## Ràng buộc và tính năng mở rộng

- **Tránh tuyến/ga:** Lọc edges có `line` hoặc node bị đánh dấu trước khi chạy thuật toán.
- **Đi qua điểm trung gian:** Chia thành nhiều đoạn, chạy A\* lần lượt, nối kết quả.
- **Dynamic rerouting:** Khi người dùng báo sự cố, loại edge/node tương ứng và chạy lại.

---

## Quy tắc làm việc

- Không sửa file trong `data/processed/` — đây là output của nhóm Dữ liệu.
- Không mock dữ liệu; luôn đọc trực tiếp từ `adjacency_list.json`.
- Hàm thuật toán phải **pure** (không side-effect, không đọc file) — nhận graph dict làm tham số.
- Đơn vị nhất quán: **km** cho weight, **[lon, lat]** cho tọa độ.