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

**Bước 6:** Chạy file tuỳ ý.  
python *file_path*.py