# Moscow Metro Pathfinder

Hệ thống tìm đường và mô phỏng sự cố mạng lưới Tàu điện ngầm Moscow.

---

## Cài đặt

**Bước 1:** Clone dự án

```bash
git clone https://github.com/cacancap/Moscow_Metro_Pathfinder.git
cd Moscow_Metro_Pathfinder
```

**Bước 2:** Tạo môi trường ảo

```bash
# Không dùng Anaconda
python -m venv venv
venv\Scripts\activate        # Windows
source venv/Scripts/activate # Git Bash / Linux / Mac

# Hoặc dùng Conda
conda create -n Moscow_Metro_Pathfinder python=3.13
conda activate Moscow_Metro_Pathfinder
```

**Bước 3:** Cài thư viện

```bash
pip install -r requirements.txt
```

---

## Chạy ứng dụng

```bash
python run.py
```

Hoặc double-click `run.bat` (Windows) / `./run.sh` (Linux/Mac).

| URL | Mô tả |
|---|---|
| http://localhost:5000 | Web App |
| http://localhost:5000/docs | Swagger API Docs |

---

## Tài khoản mặc định

| Username | Password | Quyền |
|---|---|---|
| `admin` | `admin12321` | Admin — đóng/mở ga và cạnh, thả bom |
| bất kỳ | bất kỳ | User — tìm đường |

---

## Tính năng

- **Tìm đường** — A\*, Dijkstra, BFS; đường đi hiển thị **màu theo từng tuyến metro** (viền trắng nổi bật)
- **Bản đồ tương tác** — marker ga màu theo tuyến, click để xem chi tiết
- **Hiển thị đường ray** — bật mặc định khi load; toggle ẩn/hiện; click cạnh → xem trạng thái, admin đóng/mở
- **Dropdown ga đích thông minh** — hiển thị tất cả ga chưa bị chặn; cảnh báo khi ga đích không thể đến được
- **Mô phỏng sự cố** — admin đóng/mở ga và cạnh trực tiếp trên bản đồ
- **Bomb system** — admin thả bom với bán kính tùy chọn, tự động block ga và đường trong vùng nổ
- **Closure summary** — chip ga/cạnh bị đóng có thể click để mở panel chi tiết ngay

---

## Kiến trúc

```
python run.py
  └─> uvicorn server:app --port 5000
        ├── /                  → map.html (redirect)
        ├── /api/stations      → danh sách stop nodes
        ├── /api/station_list  → catalog ga đầy đủ
        ├── /api/edge_list     → danh sách cạnh
        ├── /api/find-path     → tìm đường (POST)
        ├── /api/nearest-station → ga gần nhất (GET)
        └── /api/admin/bomb-closure → tính vùng nổ (POST)
```

Dữ liệu load từ `moscow_metro.db` (SQLite) vào RAM khi startup.

---

## Tài liệu kỹ thuật

| File | Nội dung |
|---|---|
| `docs/standards/api_contracts.md` | Hợp đồng API — endpoints, request/response |
| `docs/standards/data_contracts.md` | Schema dữ liệu — edge_list, station_dict… |
| `docs/standards/AGENTS.md` | Quy tắc làm việc cho AI agent |
| `.claude/CLAUDE.md` | Hướng dẫn chi tiết cho AI assistant |
