🚀 Task: [Tên Task Ngắn Gọn]
1. Context & Problem Statement
Bối cảnh: Mô tả vị trí của task trong Pipeline hoặc UI.

Vấn đề & Nguyên nhân: Tại sao cần thực hiện task này?

2. Objective (Mục tiêu)
Kết quả kỳ vọng: Hệ thống thay đổi ra sao?

Sản phẩm: File/Module nào được sinh ra hoặc chỉnh sửa?

3. Inputs & Outputs
- **Input:**
    - Mô tả: [Mô tả dữ liệu đầu vào]
    - Đường dẫn: [Đường dẫn file đầu vào]
- **Output:**
    - Mô tả: [Mô tả kết quả đầu ra]
    - Đường dẫn: [Đường dẫn file đầu ra]

4. Workflow Protocol (Quy trình bắt buộc)
Trạng thái Log: [ ] Đã tạo file Logs/[tên-task].md.

Phê duyệt: ⚠️ Dừng lại tại đây. Chỉ thực hiện các bước tiếp theo sau khi User phản hồi "Đồng ý" (Agree).

5. Execution Plan (Kế hoạch thực hiện)
[ ] Bước 1 (Khởi tạo): Viết bản thảo task vào thư mục Logs/.

[ ] Bước 2 (Thực thi): Chỉnh sửa logic/code tại các file liên quan (sau khi được duyệt).

[ ] Bước 3 (Hậu kỳ): Cập nhật kết quả thực tế vào file Log và đóng Task.

6. Constraints & Resources
Ràng buộc: 
- (Ví dụ: Bán kính chuyển tuyến 200m, Penalty 600m...).
- **Workspace Isolation:** Sử dụng thư mục cá nhân `data/processed/[User_Name]/` cho các file output trung gian của task để tránh xung đột khi làm việc nhóm.

Files liên quan: [Đường dẫn cụ thể trong repo].

7. Definition of Done (DoD)
[ ] File Log đã được lưu đúng vị trí: Logs/[tên-task].md.

[ ] Code pass qua các bài test liên thông.

[ ] User đã xác nhận kết quả cuối cùng.
