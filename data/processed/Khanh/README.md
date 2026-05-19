# Moscow Metro Data Pipeline - Khanh's Workspace

Thư mục này chứa toàn bộ quy trình xử lý dữ liệu từ OSM thô sang đồ thị mạng lưới tàu điện ngầm Moscow hoàn chỉnh.

## 📂 Cấu trúc Pipeline

### 1. `01_raw_extracted/`
Dữ liệu được lọc sạch từ GeoJSON gốc, tập trung vào các thực thể cốt lõi.
- `stations_raw.json`: Danh sách các ga chính.
- `stops_raw.json`: Danh sách các điểm dừng trên đường ray.
- `tracks_raw.json`: Hình học các đoạn đường ray.
- `lines_raw.json`: Metadata về các tuyến (màu sắc, tên).

### 2. `02_normalized/`
Dữ liệu đã được chuẩn hóa tọa độ (6 chữ số thập phân) và xây dựng topology.
- **Logic khớp nối:** Kết nối Ga (`station`) và Điểm dừng (`stop`) dựa trên **Tên tiếng Nga + Màu sắc** (quy đổi về mã HEX). Nếu trùng tên, hệ thống tự động chọn ga có khoảng cách gần nhất để đảm bảo tính chính xác (xử lý triệt để các ga trùng tên khác tuyến).
- `nodes_normalized.json`: Danh sách đỉnh duy nhất toàn mạng lưới.
- `edges_normalized.json`: Danh sách cạnh đã được nối (bao gồm cả các đoạn vá thủ công để thông tuyến).

### 3. `03_connected_network/`
Đồ thị đã được liên thông hóa thông qua các Virtual Hubs.
- **Logic gom nhóm (Clustering):** Sử dụng thuật toán **Single-linkage Clustering** với bán kính **230 mét**. Một ga sẽ gia nhập cụm trung chuyển nếu nó nằm gần *bất kỳ* thành viên nào trong cụm đó dưới 300m (không phụ thuộc vào tên).
- `nodes_with_hubs.json`: Đã bao gồm các Hub ảo trung tâm (37 Hubs).
- `edges_with_hubs.json`: Đã bao gồm các cạnh trung chuyển (transfer) giữa các ga với trọng số phạt ảo (Penalty).

### 4. `04_final_output/` (ĐẦU RA QUAN TRỌNG NHẤT)
Đây là các file dùng để lập trình thuật toán và giao diện.

#### 🚀 `adjacency_list.json`
Dùng cho: **Thuật toán A*, Dijkstra**.
- **Đơn vị trọng số (Weight):** Kilomet (km).
- Cấu trúc:
  - `nodes`: `{ "node_id": [lon, lat] }` -> Dùng để tính hàm Heuristic khoảng cách chim bay.
  - `graph`: `{ "source_id": { "target_id": weight } }` -> Truy xuất láng giềng và trọng số với tốc độ O(1).

#### 🎨 `station_metadata.json`
Dùng cho: **Giao diện Streamlit, Hiển thị bản đồ**.
- Chứa: Tên tiếng Nga/Anh, tọa độ hiển thị, loại node và danh sách các tuyến đi qua ga đó.

---

## 🛠 Cách chạy lại Pipeline
Toàn bộ script nằm trong thư mục `scripts/`. Để chạy lại toàn bộ quy trình, hãy thực hiện theo thứ tự:
1. `extract_raw.py`
2. `normalize_graph.py`
3. `apply_manual_patch.py` (Vá Tuyến 3)
4. `create_transfer_hubs.py`
5. `package_data.py`
6. `verify_graph.py` (Kiểm định)

## 📊 Báo cáo
Xem các báo cáo về đứt gãy và tính liên thông trong thư mục `reports/`.
- `validation_results.txt`: Xác nhận tính liên thông 100% của mạng lưới.
