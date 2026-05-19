# Frontend — Moscow Metro Pathfinder

## Tổng quan

Giao diện web thuần HTML/CSS/JS, phục vụ qua Flask (`web/app.py`). Không dùng framework frontend.

---

## Cấu trúc thư mục `web/`

```
web/
  index.html      # Trang đăng nhập (route: /)
  map.html        # Trang bản đồ chính (route: /map.html)
  admin.html      # Trang quản trị (route: /admin.html)
  style.css       # Toàn bộ CSS — design system với theme Metro Moscow
  auth.js         # Auth, API endpoints, localStorage helpers, fetchJson()
  script.js       # Logic bản đồ — Leaflet, tìm đường, render
  admin.js        # Logic admin — đóng ga, chặn cạnh
```

---

## Design system (`style.css`)

### Màu sắc
| Biến | Giá trị | Dùng cho |
|---|---|---|
| `--red` | `#c8102e` | Accent chính (Moscow Metro đỏ) |
| `--text` | `#1b1f2d` | Chữ chính |
| `--muted` | `#7b8899` | Chữ phụ, label |
| `--surface` | `#ffffff` | Nền card/panel |
| `--surface-soft` | `#f6f8fb` | Nền panel body |
| `--border` | `rgba(10,20,40,.09)` | Viền mỏng |

### Components
- `.btn .btn-primary / .btn-ghost / .btn-danger` — buttons
- `.field` — label + input/select
- `.glass-panel .route-panel` — side panel trái
- `.status-card .workspace-card` — card bên trong panel
- `.chip .chip-muted / .chip-action` — tag nhỏ
- `.line-dot` — chấm tròn màu tuyến metro
- `.result-item` — item trong danh sách tìm kiếm
- `.route-station-item` — item ga trong lộ trình

---

## Luồng xác thực

- **Bất kỳ username** + bất kỳ password → role `user` → redirect `map.html`
- **admin** + **admin12321** → role `admin` → redirect `admin.html`
- Role và username lưu `localStorage` với keys `metro_user_role`, `metro_username`

---

## API endpoints được gọi

| Endpoint | Method | Dùng trong | Mô tả |
|---|---|---|---|
| `/api/network-summary` | GET | `script.js`, `admin.js` | Thống kê mạng lưới |
| `/api/stations` | GET | `script.js`, `admin.js` | Danh sách stop nodes |
| `/api/station_list` | GET | `script.js`, `admin.js` | Catalog ga (nhóm theo tuyến) |
| `/api/edge_list` | GET | `script.js`, `admin.js` | Danh sách cạnh kèm geometry |
| `/api/find-path` | POST | `script.js` | Tìm đường A* |
| `/api/health` | GET | — | Health check |

---

## Tính năng chính (`map.html`)

1. **Tìm ga** — search box lọc theo tên Nga/Anh, hiện kết quả với chấm màu tuyến
2. **Chọn ga đi/đến** — dropdown hoặc click marker trên bản đồ
3. **Tìm đường** — gọi `/api/find-path`, vẽ polyline + marker trên Leaflet
4. **Danh sách ga** — liệt kê theo thứ tự với chấm màu tuyến
5. **Lịch sử** — 6 lộ trình gần nhất (localStorage)
6. **Đóng ga từ panel** — chỉ hiện nút "Đóng ga" khi role admin

## Tính năng admin (`admin.html`)

1. Tìm kiếm ga → click thêm vào danh sách đóng
2. Tìm kiếm cạnh → click thêm vào danh sách chặn
3. **Lưu** → ghi vào `localStorage` → `script.js` đọc khi tìm đường

---

## Màu tuyến — `resolveLineColor()` trong `script.js`

| Tên màu (data) | Hex |
|---|---|
| red | #ff4d4d |
| blue | #4f8cff |
| lightblue | #62d0ff |
| green | #34c47c |
| orange | #ff9d42 |
| yellow | #f6d64a |
| violet | #9d72ff |
| brown | #9a684a |
| purple | #8f7aff |

---

## Cách chạy

```bash
python run.py
# hoặc
uvicorn server:app --port 5000
# hoặc  
python web/app.py
```

Truy cập: `http://localhost:5000`
