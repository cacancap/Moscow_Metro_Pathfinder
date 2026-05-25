import uvicorn

if __name__ == '__main__':
    print("🚀 Đang khởi động Server FastAPI (Moscow Metro V2)...")
    # "api:app" nghĩa là tìm biến 'app' ở trong file 'api.py'
    # Chạy ở cổng 5000 để khớp 100% với file auth.js bên Frontend
    uvicorn.run("api:app", host="127.0.0.1", port=5000, reload=True)