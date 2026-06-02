# AGENTS Working Rules

Quy tắc bắt buộc cho AI agents làm việc trong repository này.

## 0) Giao việc (human → agent)

Dùng skeleton **Goal / Scope / Non-goals / Acceptance / Verify** trong [task_template.md](task_template.md). Ưu tiên tiếng Anh cho anchor kỹ thuật (path, endpoint, field name); intent sản phẩm có thể dùng tiếng Việt.

## 1) Approval-First

- Không sửa code hoặc cấu hình nếu user chưa xác nhận rõ ràng.
- Với task không trivial: đề xuất plan trước, chờ duyệt rồi mới implement.
- Nếu yêu cầu không rõ: hỏi trước khi làm.

## 2) Minimal Change

- Luôn ưu tiên diff nhỏ nhất giải quyết đúng vấn đề.
- Không refactor rộng khi fix nhỏ là đủ.
- Giữ nguyên behavior trừ khi thay đổi được yêu cầu tường minh.

## 3) Báo cáo sau mỗi task

Sau khi implement, report:
- Đã thay đổi gì và tại sao.
- Logic flow mới hoạt động như thế nào.
- Lệnh verify (run/test) và kết quả chính.

## 4) Main Runtime Flow (Source of Truth)

```
python run.py
  └─> uvicorn server:app --host 127.0.0.1 --port 5000 --reload
```

**Một server duy nhất** (`server.py`) phục vụ cả API lẫn file tĩnh (`web/`).

> ⚠️ Không còn kiến trúc cũ: `api.py` (port 8000) + `web/app.py` Flask (port 5000).

Files ngoài flow này không được sửa trừ khi user yêu cầu.

## 5) Các file cốt lõi cần biết

| File | Vai trò |
|---|---|
| `server.py` | FastAPI app duy nhất — API + static serving |
| `web/script.js` | Logic bản đồ, routing, edge layer, bomb |
| `web/admin.js` | Dashboard quản lý đóng ga/cạnh |
| `web/auth.js` | Auth helpers, API endpoints, localStorage utils |
| `web/map.html` | Bản đồ chính (user + admin view) |
| `web/style.css` | Design system (red `#c8102e`, Manrope/Space Grotesk) |
| `moscow_metro.db` | SQLite — nguồn dữ liệu runtime (không chỉnh tay) |

## 6) Quy tắc Frontend quan trọng

- **Tọa độ:** data là `[lon, lat]` (GeoJSON); Leaflet dùng `[lat, lon]` — luôn đảo khi vẽ.
- **Blocked state:** đọc qua `getEffectiveBlockedConfig()` (gộp manual + bomb), ghi qua `saveBlockedConfig()`. Không truy cập localStorage trực tiếp cho blocked data.
- **Bomb-blocked guard:** khi toggle đóng/mở ga hoặc cạnh, luôn kiểm tra item có đang bị bomb-blocked không (có trong effective nhưng không có trong manual config). Nếu có → không cho mở thủ công.
- **Edge layer:** dùng `refreshEdgeVisuals()` sau bất kỳ thay đổi blocked edges nào nếu layer đang hiển thị.
- **Edge click:** dùng `onMapEdgeClick()` (map-level, hit-test pixel) — KHÔNG dùng hitArea Leaflet polyline cho edge click vì overlayPane canvas (z-index 400) không nhận browser click khi markerPane canvas (z-index 600) đang ở trên. Xem `ptSegDistPx()` để tham khảo thuật toán.
- **Station click priority:** `state.stationClicked` flag — set trong `marker.on("click")` với `setTimeout(..., 0)` reset. Kiểm tra trong `onMapEdgeClick()` để tránh mở edge panel khi station được click.
- **Route pane:** route path render trong `routePane` (z-index 450, tạo trong `buildMap()`). Đặt giữa overlayPane (400) và markerPane (600) để route luôn đè lên edge layer.
- **Browser cache:** khi thêm hàm JS mới, tăng `?v=N` trong `<script src>` của `map.html`. Phiên bản hiện tại: `script.js?v=9`.

## 7) Safety & Scope

- Không chạy destructive operations.
- Không commit/push trừ khi được yêu cầu rõ ràng.
- Giữ nguyên style và tổ chức file hiện tại.
- Cập nhật docs khi thay đổi API contract hoặc tính năng lớn.

## 8) Completion Checklist

Trước khi báo hoàn thành:

- [ ] Tuân thủ approval-first và minimal-change.
- [ ] Runtime flow vẫn hợp lệ (`python run.py` → `server.py` port 5000).
- [ ] Docs (api_contracts, data_contracts, CLAUDE.md) đã cập nhật nếu có thay đổi contract.
- [ ] Có verification steps cụ thể.
