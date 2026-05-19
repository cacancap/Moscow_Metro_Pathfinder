# Moscow Metro Pathfinder - Kế hoạch Xử lý Dữ liệu & Kiến trúc Hệ thống

Dự án này nhằm mục tiêu xây dựng một công cụ tìm đường tối ưu cho mạng lưới tàu điện ngầm Moscow dựa trên dữ liệu OpenStreetMap (OSM).

---

## 🚀 Giai đoạn 1: Trích xuất và Phân tách dữ liệu thô (Raw Extraction)
*Mục tiêu: Lọc nhiễu để lấy ra các thực thể cốt lõi từ tệp GeoJSON.*

1.  **Trích xuất Ga (Nodes):**
    *   Lọc các thực thể có tag `railway=station` và `station=subway`.
    *   Lưu trữ: `osm_id`, tọa độ (`lat`, `lon`), tên (`name:ru`, `name:en`) và thuộc tính `colour`.
2.  **Trích xuất Điểm dừng (Stops):**
    *   Lọc các node `railway=stop` từ tệp Relation để lấy tọa độ chính xác trên ray và màu sắc tuyến (HEX).
3.  **Trích xuất Đường ray (Ways):**
    *   Lọc các đường có tag `railway=subway`. Lưu trữ danh sách tọa độ để tạo cạnh.

---

## 🛠 Giai đoạn 2: Chuẩn hóa Đỉnh và Cạnh (Normalization)
*Mục tiêu: Chuyển đổi dữ liệu địa lý thành cấu trúc đồ thị Station-Stop-Way.*

1.  **Xử lý Tọa độ và Đỉnh (Vertices):**
    *   **Làm tròn tọa độ:** Đưa tất cả tọa độ về độ chính xác 6 chữ số thập phân (~10cm).
    *   **Logic khớp nối (Matching):** Kết nối Ga (`station`) và Điểm dừng (`stop`) dựa trên **Tên tiếng Nga + Màu sắc** (quy đổi tên màu OSM sang HEX). Nếu trùng tên, sử dụng khoảng cách gần nhất để định danh chính xác (giải quyết lỗi ga trùng tên khác tuyến).
    *   **Global Node Registry:** Đăng ký tất cả các điểm tọa độ vào một Registry duy nhất để đảm bảo tính liên thông tự nhiên giữa các đoạn Ray (Way).
2.  **Xây dựng Đồ thị Đa tầng (Multi-layer Graph):**
    *   **Cạnh Platform (Station to Stop):** Trọng số ≈ 0.
    *   **Cạnh Track (Stop to Stop):** Trọng số là khoảng cách vật lý thực tế.
3.  **Vá lỗi mạng lưới (Network Patching):**
    *   Thực hiện tạo các cạnh "Cầu nối" (Bridge Edges) thủ công cho các vị trí dữ liệu OSM bị đứt quãng (ví dụ: Tuyến số 3 đoạn ga Mitino) để đảm bảo liên thông 100%.

---

## 🔄 Giai đoạn 3: Xây dựng Logic Chuyển tuyến (Transfer Hubs)
*Mục tiêu: Kết nối các tuyến rời rạc thông qua mô hình Virtual Hub Node.*

1.  **Thuật toán Gom cụm (Clustering):**
    *   Sử dụng thuật toán **Single-linkage Clustering** với bán kính **300 mét**. 
    *   Một ga sẽ gia nhập cụm trung chuyển nếu nó nằm gần *bất kỳ* thành viên nào trong cụm đó dưới 200m (không phụ thuộc vào tên ga).
2.  **Mô hình Hub ảo:**
    *   Mỗi cụm trung chuyển được đại diện bởi một **Hub Node ảo** đặt tại tâm cụm.
    *   Thiết lập cạnh Station <-> Hub với trọng số phạt (Transfer Penalty) tương đương 3km ảo để mô phỏng thời gian đi bộ và chờ tàu.

---

## 📦 Giai đoạn 4: Đóng gói Dữ liệu Lai (Hybrid Data Packaging)
*Mục tiêu: Xuất dữ liệu tối ưu cho ứng dụng Streamlit.*

1.  **Tệp `adjacency_list.json` (Cho thuật toán):**
    *   Cấu trúc từ điển lồng nhau phục vụ tra cứu $O(1)$.
    *   **Đơn vị trọng số:** Kilomet (km).
    *   Đính kèm tọa độ node hỗ trợ Heuristic cho thuật toán **A***.
2.  **Tệp `station_metadata.json` (Cho UI):**
    *   Chứa thông tin hiển thị: Tên đa ngôn ngữ, danh sách tuyến đi qua và màu sắc đặc trưng.

---

## ✅ Giai đoạn 5: Kiểm định và Thử nghiệm (Validation)
*Mục tiêu: Đảm bảo tính liên thông và hiệu năng mạng lưới.*

1.  **Connectivity Check:** Sử dụng **BFS** để đảm bảo 100% ga chính có thể đi đến nhau.
2.  **Performance Benchmark:** Đảm bảo thời gian tìm đường trung bình đạt mức mil giây (kỳ vọng < 0.01s).

---
*Kế hoạch này đảm bảo tính chính xác về mặt topology và tối ưu hiệu năng cho hệ thống tìm đường.*
