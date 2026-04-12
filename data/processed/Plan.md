# Moscow Metro Pathfinder - Kế hoạch Xử lý Dữ liệu & Kiến trúc Hệ thống

Dự án này nhằm mục tiêu xây dựng một công cụ tìm đường tối ưu cho mạng lưới tàu điện ngầm Moscow dựa trên dữ liệu OpenStreetMap (OSM).

---

## 🚀 Giai đoạn 1: Trích xuất và Phân tách dữ liệu thô (Raw Extraction)
*Mục tiêu: Lọc nhiễu để lấy ra các thực thể cốt lõi từ tệp GeoJSON.*

1.  **Trích xuất Ga (Nodes):**
    *   Lọc các thực thể có tag `railway=station` và `station=subway`.
    *   Lưu trữ: `osm_id`, tọa độ (`lat`, `lon`), tên (`name:ru`, `name:en`).
    *   **Lưu ý:** Ánh xạ các `stop_position` (điểm dừng trên ray) về ga chính để đơn giản hóa đồ thị.
2.  **Trích xuất Đường ray (Ways):**
    *   Lọc các đường có tag `railway=subway`.
    *   Lưu trữ danh sách các node tạo thành đoạn ray để phục vụ vẽ bản đồ.
3.  **Metadata Tuyến:**
    *   Thu thập `line_id`, `colour` (mã HEX), `operator` từ các Relation để hiển thị UI chuẩn thương hiệu Moscow Metro.

---

## 🛠 Giai đoạn 2: Chuẩn hóa Đỉnh và Cạnh (Normalization)
*Mục tiêu: Chuyển đổi dữ liệu địa lý thành cấu trúc đồ thị toán học.*

1.  **Xác định Đỉnh (Vertices):**
    *   Mỗi ga tàu là một đỉnh chính trong đồ thị.
    *   Loại bỏ các "Shape Points" khỏi logic tính toán đường đi, chỉ giữ lại để vẽ đường cong trên UI.
2.  **Tính toán trọng số (Weighting):**
    *   Sử dụng công thức **Haversine** để tính khoảng cách vật lý giữa các ga kế cận trên cùng một tuyến.
3.  **Xử lý hướng (Directionality):**
    *   Kiểm tra tag `oneway`. Mặc định tạo cạnh hai chiều trừ khi có tag `oneway=yes`.

---

## 🔄 Giai đoạn 3: Xây dựng Logic Chuyển tuyến (Transfer Clustering)
*Mục tiêu: Kết nối các tuyến rời rạc thành một mạng lưới thống nhất.*

1.  **Thuật toán láng giềng gần:**
    *   Sử dụng **KD-Tree** để tìm các ga khác tuyến trong bán kính 200m.
2.  **Tạo Cạnh ảo (Virtual Edges):**
    *   Thiết lập kết nối giữa các ga chuyển tuyến (Transfer Hubs).
    *   **Lưu ý:** Xử lý các cụm ga có tên khác nhau nhưng thông nhau (ví dụ: *Biblioteka Imeni Lenina* & *Arbatskaya*).
3.  **Gán Trọng số phạt (Transfer Penalty):**
    *   **Công thức:** $Weight = Distance(km) + Penalty\_Factor$
    *   *Penalty Factor:* Tương đương 3-5 phút di chuyển (khoảng 2-3km ảo) để phản ánh thời gian đi bộ và chờ tàu.
    *   *Đặc biệt:* Tăng Penalty cho các ga trung chuyển sang tuyến MCC (Tuyến 14) do khoảng cách đi bộ lớn.

---

## 📦 Giai đoạn 4: Đóng gói Dữ liệu Lai (Hybrid Data Packaging)
*Mục tiêu: Xuất dữ liệu tối ưu cho ứng dụng Streamlit.*

1.  **Tệp `adjacency_list.json` (Cho thuật toán):**
    *   Cấu trúc tối giản: `source_id`, `target_id`, `weight`.
    *   Bổ sung tọa độ để hỗ trợ hàm Heuristic cho thuật toán **A***.
2.  **Tệp `station_metadata.json` (Cho UI):**
    *   Chứa thông tin hiển thị: Tên ga, màu tuyến, tọa độ thực, và hình học đường ray (`geometry`).
3.  **Đồng bộ hóa ID:**
    *   Sử dụng OSM ID đồng nhất giữa các tệp để truy xuất chéo tức thì.

---

## ✅ Giai đoạn 5: Kiểm định và Thử nghiệm (Validation)
*Mục tiêu: Đảm bảo tính liên thông và độ chính xác của kết quả.*

1.  **Connectivity Check:**
    *   Sử dụng **BFS** để đảm bảo mọi ga đều có thể đi đến nhau.
2.  **Kịch bản Vòng tròn (Circle Lines):**
    *   Kiểm tra logic tìm đường trên Tuyến 5 (Koltsevaya) và Tuyến 11 (Big Circle) để tránh lỗi vòng lặp hoặc chọn hướng đi xa hơn.
3.  **Performance Benchmark:**
    *   Đảm bảo thời gian nạp dữ liệu và tìm đường không quá **2 giây** trên Streamlit.

---
*Kế hoạch này được thiết kế để tách biệt Logic tính toán và Hiển thị, đảm bảo hệ thống có thể mở rộng và bảo trì dễ dàng.*
