const routeGroup = L.layerGroup().addTo(map); // Chứa đường đi và 2 điểm chọn
let selectedNodes = []; // Mảng lưu trữ 2 điểm [latlng1, latlng2]

function enablePathfindingMode() {
    // Xóa sạch dữ liệu cũ trước khi bắt đầu chế độ mới
    clearPathfinding();

    // Lắng nghe sự kiện click trên toàn bản đồ
    map.on('click', onMapClickForPath);
}

/**
 * Xử lý sự kiện click khi đang trong chế độ tìm đường
 */
function onMapClickForPath(e) {
    const clickedLatLng = e.latlng;

    // 1. Thêm điểm vào danh sách lựa chọn
    selectedNodes.push(clickedLatLng);

    // 2. Vẽ Marker tại điểm vừa click và cho vào routeGroup
    const marker = L.marker(clickedLatLng, {
        icon: L.divIcon({
            className: 'custom-icon',
            html: `<div style="background-color: ${selectedNodes.length === 1 ? 'blue' : 'green'}; 
                   width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`
        })
    }).addTo(routeGroup);
    
    marker.bindPopup(selectedNodes.length === 1 ? "Điểm xuất phát" : "Điểm đích").openPopup();

    // 3. Nếu đã chọn đủ 2 điểm
    if (selectedNodes.length === 2) {
        // Tắt sự kiện click để không chọn thêm điểm thứ 3
        map.off('click', onMapClickForPath);

        // THỰC HIỆN KẾT NỐI
        processPathfinding(selectedNodes[0], selectedNodes[1]);
    }
}

/**
 * Hàm xử lý logic chính (Vẽ đường hoặc Gọi Python API)
 */
async function processPathfinding(start, end) {
    console.log("Đang tìm đường từ:", start, "đến:", end);

    // --- PHẦN DEMO: Nối trực tiếp 2 điểm ---
    const demoPath = [start, end];
    const polyline = L.polyline(demoPath, {
        color: '#2ecc71',
        weight: 6,
        dashArray: '10, 10', // Đường đứt nét cho đẹp
        opacity: 0.8
    }).addTo(routeGroup);

    // Tự động căn chỉnh bản đồ để thấy cả 2 điểm
    map.fitBounds(polyline.getBounds(), { padding: [50, 50] });

    /* --- PHẦN THỰC TẾ (KHI CÓ PYTHON SERVER) ---
    try {
        const response = await fetch(`http://127.0.0.1:5000/api/path?s_lat=${start.lat}&s_lng=${start.lng}&e_lat=${end.lat}&e_lng=${end.lng}`);
        const data = await response.json();
        // Xóa đường demo và vẽ đường thật từ data.path
        routeGroup.clearLayers(); 
        L.polyline(data.path, {color: 'green'}).addTo(routeGroup);
    } catch (err) { console.error(err); }
    */
}

/**
 * Hàm dọn dẹp sạch sẽ
 */
function clearPathfinding() {
    selectedNodes = []; // Reset mảng tọa độ
    routeGroup.clearLayers(); // Xóa sạch Marker và Polyline trên bản đồ
    map.off('click', onMapClickForPath); // Hủy lắng nghe sự kiện click
}