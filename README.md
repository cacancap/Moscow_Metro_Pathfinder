## Hướng dẫn cài đặt và chạy dự án

**Bước 1:** Clone dự án về máy
git clone https://github.com/cacancap/Moscow_Metro_Pathfinder.git  
cd Moscow_Metro_Pathfinder

**Bước 2:** Tạo và kích hoạt môi trường ảo
Mở Terminal trong thư mục dự án  
python -m venv venv  
venv\Scripts\activate   # (Dùng source venv/Scripts/activate nếu dùng Git Bash)

**Bước 3:** Cài đặt toàn bộ thư viện cần thiết chỉ với 1 lệnh
pip install -r requirements.txt

**Bước 4:** Chạy ứng dụng Streamlit
streamlit run web/app.py
