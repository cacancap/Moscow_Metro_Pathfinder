# 🚇 Dự án: Moscow Metro Pathfinder

## 1. Tổng quan dự án (Project Overview)
- **Mục tiêu:** Xây dựng hệ thống tìm đường (routing) và trực quan hóa bản đồ cho mạng lưới Tàu điện ngầm Moscow.
- **Backend/Data:** Xử lý dữ liệu không gian OSM (GeoJSON), xây dựng đồ thị (Adjacency List, Haversine distance), tính toán chi phí và chạy thuật toán tìm đường (FastAPI/Python).
- **Frontend (Current Focus):** Giao diện người dùng để chọn ga đi/đến, hiển thị bản đồ tương tác và vẽ lộ trình.

## 2. Cấu trúc thư mục cốt lõi (Directory Structure)
Mọi tệp tin đều nằm trong thư mục gốc `.MOSCOW_METRO_PATHFINDER/`:  

├── algorithm/      # Chứa thuật toán cốt lõi (Dijkstra, A*, DFS/BFS)  
├── data/           # Pipeline dữ liệu  
│   ├── processed/  
│   └── raw/        # Dữ liệu GeoJSON gốc từ OSM  
├── docs/           # Tài liệu dự án  
└── web/       

MOSCOW_METRO_PATHFINDER/  
├── algorithm/  # Chứa các file thuật toán của dự án
├── data/
│   ├── mock/
│   ├── processed/  # Dữ liệu JSON đã tinh chế (edge_list, station_dict, adjacency_list...)  
│   └── raw/
├── web/
├── .gitignore
├── api.py
├── CLAUDE.md
├── README.md
├── requirements.txt
├── run.bat
├── run.py
├── run.sh
└── server.py

## 3. Ngăn xếp công nghệ (Tech Stack)
- **Backend/Data:** Python 3.13, FastAPI.
- **Frontend:** [Điền framework/thư viện của bạn vào đây, VD: HTML/CSS/JS thuần, React, Vue, TailwindCSS]
- **Bản đồ (Mapping):** [Điền thư viện bản đồ, VD: Leaflet.js, Mapbox GL JS, D3.js]

## 4. Quy ước Code (Coding Standards)
### Chung:
- Suy nghĩ theo từng bước (Think step-by-step) trước khi viết code.
- Luôn ưu tiên hiệu suất và tối ưu bộ nhớ, đặc biệt khi xử lý JSON đồ thị lớn.
- Viết comment bằng tiếng Việt cho các logic phức tạp, tên biến/hàm viết bằng tiếng Anh.

### Frontend:
- Tách biệt logic API (gọi dữ liệu backend/JSON) ra khỏi UI Components.
- Khi xử lý tọa độ từ `station_dict.json`, lưu ý định dạng là `[lon, lat]` (chuẩn GeoJSON). Một số thư viện bản đồ (như Leaflet) lại yêu cầu `[lat, lon]`. Luôn kiểm tra kỹ bước đảo ngược này.
- [Thêm các quy tắc UI/UX cụ thể của bạn tại đây]

## 5. Nhiệm vụ hiện tại (Current Mission)
- **Mục tiêu ngắn hạn:** Xây dựng giao diện tương tác cơ bản (Frontend) để load dữ liệu `station_dict.json` và hiển thị các ga lên bản đồ.
- **Ngữ cảnh bổ sung:** Chú ý các ga trung chuyển (transfer) và các ga có chung tên tiếng Nga nhưng khác mã màu (colour/line_id).

## 6. Lệnh thường dùng (Common Commands)
- [Điền lệnh chạy Frontend, VD: `npm run dev` hoặc `python -m http.server`]
- [Điền lệnh chạy Backend, VD: `uvicorn main:app --reload`]