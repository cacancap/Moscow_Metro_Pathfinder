// 1. Khởi tạo bản đồ
// Hà Nội [21.0285, 105.8542]
// Moscow [55.7558, 37.6173]
const map = L.map('map').setView([55.7558, 37.6173], 13);

// 2. Thêm lớp bản đồ từ OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// 3. Thêm Marker (điểm đánh dấu)
let marker = L.marker([55.788503,37.7509929]).addTo(map);
marker.bindPopup("<b>Chào bạn!</b><br>Đây là Moscow.").openPopup();

map.on('click', function(e) {
    // 1. Lấy tọa độ từ sự kiện click
    let lat = e.latlng.lat;
    let lng = e.latlng.lng;
    if(marker){
        // 2. Di chuyển Marker đến vị trí vừa click
        marker.setLatLng([lat, lng]);
    } else {
        // Nếu chưa có Marker thì tạo mới
        marker = L.marker([lat, lng]).addTo(map);
    }

    // 3. Hiển thị thông báo ngay trên bản đồ
    marker.bindPopup("Tọa độ bạn chọn: <br>Lat: " + lat.toFixed(4) + "<br>Lng: " + lng.toFixed(4))
               .openPopup();
});






