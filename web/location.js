let userMarker = null; // Biến toàn cục để lưu Marker của người dùng


// Hàm kích hoạt định vị
function getLocation() {
    const x = document.getElementById("myLocation");
    if (navigator.geolocation) {
        x.innerHTML = "Đang xác định vị trí...";
        navigator.geolocation.getCurrentPosition(showPosition, showError);
    } else {
        x.innerHTML = "Trình duyệt không hỗ trợ định vị.";
    }
}

// Hàm xử lý khi lấy được tọa độ thành công
function showPosition(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;
    const x = document.getElementById("myLocation");

    x.innerHTML = `Vĩ độ: ${lat.toFixed(4)} <br> Kinh độ: ${lng.toFixed(4)}`;

    // 2. Di chuyển bản đồ về vị trí hiện tại
    map.setView([lat, lng], 15); // Zoom vào mức 15 để thấy rõ

    // 3. Xử lý Marker
    if (userMarker) {
        // Nếu đã có Marker rồi thì chỉ cập nhật vị trí
        userMarker.setLatLng([lat, lng]).update();
    } else {
        // Nếu chưa có thì tạo mới Marker với icon khác biệt 
        userMarker = L.circleMarker([lat, lng], {
            radius: 10,
            fillColor: "#ff0000",
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        }).addTo(map);
        
    }
    
    userMarker.bindPopup("<b>Bạn đang ở đây!</b>").openPopup();
}

// Hàm xử lý các lỗi định vị    
function showError(error) {
    const x = document.getElementById("myLocation");
    switch(error.code) {
        case error.PERMISSION_DENIED:
            x.innerHTML = "Bạn đã từ chối quyền truy cập vị trí.";
            break;
        case error.POSITION_UNAVAILABLE:
            x.innerHTML = "Không tìm thấy thông tin vị trí.";
            break;
        case error.TIMEOUT:
            x.innerHTML = "Hết thời gian yêu cầu.";
            break;
        default:
            x.innerHTML = "Lỗi không xác định.";
            break;
    }
}