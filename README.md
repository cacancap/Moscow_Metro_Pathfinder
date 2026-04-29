# Hướng dẫn cài đặt và chạy dự án


**Bước 1:** Clone dự án về máy
git clone https://github.com/cacancap/Moscow_Metro_Pathfinder.git  
cd Moscow_Metro_Pathfinder


**Bước 2:** Tạo và kích hoạt môi trường ảo  

## Cách 1: Không dùng Anaconda
**Bước 3:** Mở Terminal trong thư mục dự án  
python -m venv venv  
venv\Scripts\activate   # (Dùng source venv/Scripts/activate nếu dùng Git Bash)

**Bước 4:** Cài đặt toàn bộ thư viện cần thiết chỉ với 1 lệnh   
pip install -r requirements.txt

**Bước 5:** Chạy file tuỳ ý   
python *file_path*.py

## Cách 2: Dùng Anaconda  
**Bước 3:**  Mở Terminal, kích hoạt base.    
Gõ đường dẫn trỏ đến file Scripts\activate.bat trong Miniconda3/Anaconda3.    
- VD: D:\Python_SourceCodes\Miniconda3\Scripts\activate.bat

**Bước 4:** Tạo & kích hoạt môi trường ảo cho riêng thư mục dự án.    
conda create -n Moscow_Metro_Pathfinder python=3.13.12  
conda activate Moscow_Metro_Pathfinder  
  ***Lưu ý:*** Nhớ check bằng lệnh "conda env list" trước, kẻo trùng tên môi trường.  

**Bước 5:** Tải các gói tài nguyên cần thiết.  
1. Di chuyển vào thư mục dự án:  
   cd *directory_path*\Moscow_Metro_Pathfinder  
2. pip install -r requirements.txt

**Bước 6:** Chạy ứng dụng Moscow Metro Pathfinder

## Cách chạy đơn giản (Khuyến nghị)
Chỉ cần chạy 1 lệnh duy nhất để khởi động cả backend và frontend:

### Windows:
```bash
python run.py
```
hoặc double-click file `run.bat`

### Linux/Mac:
```bash
python run.py
```
hoặc
```bash
chmod +x run.sh
./run.sh
```

## Cách chạy riêng lẻ (Advanced)
Nếu muốn chạy riêng từng phần:

### Backend (FastAPI - Port 8000):
```bash
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend (Flask - Port 5000):
```bash
python web/app.py
```

## Truy cập ứng dụng
- **Web App**: http://localhost:5000
- **API Docs**: http://localhost:8000/docs

*