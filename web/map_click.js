/**
 * Map Click Handler — Tìm ga gần nhất từ điểm click
 */

let clickMarker = null;
let nearestStationPopup = null;

/**
 * Xử lý khi người dùng click trên bản đồ
 */
function handleMapClick(e) {
    const { lat, lng } = e.latlng;
    
    // Xóa marker cũ nếu có
    if (clickMarker) {
        map.removeLayer(clickMarker);
        clickMarker = null;
    }
    
    if (nearestStationPopup) {
        map.closePopup(nearestStationPopup);
        nearestStationPopup = null;
    }
    
    // Thêm marker mới tại điểm click
    clickMarker = L.circleMarker([lat, lng], {
        radius: 8,
        fillColor: "#ef4444",
        color: "#dc2626",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8,
    })
        .addTo(map)
        .bindPopup(
            `<div style="font-size:0.85rem; text-align:center;">
                <div><strong>Điểm Click</strong></div>
                <div>Lat: ${lat.toFixed(4)}</div>
                <div>Lon: ${lng.toFixed(4)}</div>
                <div style="margin-top: 6px; font-size: 0.75rem; color: #666;">Tìm ga gần nhất...</div>
            </div>`
        );
    
    clickMarker.openPopup();
    
    // Tìm ga gần nhất
    findNearestStation(lat, lng);
}

/**
 * Gọi API để tìm ga gần nhất
 */
async function findNearestStation(lat, lon) {
    try {
        const response = await fetch(`/api/nearest-station?lat=${lat}&lon=${lon}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const station = await response.json();
        
        // Thêm marker cho ga gần nhất
        const stationMarker = L.circleMarker([station.lat, station.lon], {
            radius: 7,
            fillColor: "#10b981",
            color: "#059669",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7,
        }).addTo(map);
        
        const popupContent = `
            <div style="font-size: 0.85rem; width: 180px;">
                <div><strong>${station.name}</strong></div>
                <div style="font-size: 0.75rem; color: #666; margin: 4px 0;">
                    ${station.name_en ? `<div>${station.name_en}</div>` : ""}
                </div>
                <div style="margin: 6px 0; padding: 6px 0; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;">
                    <strong>${formatDistanceSmall(station.distance_meters)}</strong>
                </div>
                <button type="button" onclick="setAsStart('${station.id}')" style="
                    width: 100%; padding: 4px 8px; margin-bottom: 4px;
                    background: #3b82f6; color: white; border: none; border-radius: 3px;
                    font-size: 0.75rem; cursor: pointer;
                ">Ga đi</button>
                <button type="button" onclick="setAsEnd('${station.id}')" style="
                    width: 100%; padding: 4px 8px;
                    background: #6366f1; color: white; border: none; border-radius: 3px;
                    font-size: 0.75rem; cursor: pointer;
                ">Ga đến</button>
            </div>
        `;
        
        stationMarker.bindPopup(popupContent).openPopup();
        nearestStationPopup = stationMarker;
    } catch (error) {
        console.error("Error finding nearest station:", error);
        if (clickMarker) {
            clickMarker.setPopupContent(
                `<div style="font-size:0.85rem; text-align:center; color: red;">
                    <div>Lỗi: ${error.message}</div>
                </div>`
            );
        }
    }
}

/**
 * Format khoảng cách nhỏ gọn
 */
function formatDistanceSmall(meters) {
    const m = Number(meters);
    if (m >= 1000) {
        return `${(m / 1000).toFixed(1)} km`;
    }
    return `${Math.round(m)} m`;
}

/**
 * Đặt ga gần nhất làm điểm khởi đầu
 */
function setAsStart(stationId) {
    const station = state.stationById.get(stationId);
    if (station) {
        document.getElementById("startStation").value = stationId;
        closeStationPanel();
        if (clickMarker) {
            map.removeLayer(clickMarker);
            clickMarker = null;
        }
        if (nearestStationPopup) {
            map.closePopup(nearestStationPopup);
            nearestStationPopup = null;
        }
        setStatus(`Đã chọn ga đi: ${station.name}`);
    }
}

/**
 * Đặt ga gần nhất làm điểm kết thúc
 */
function setAsEnd(stationId) {
    const station = state.stationById.get(stationId);
    if (station) {
        document.getElementById("endStation").value = stationId;
        closeStationPanel();
        if (clickMarker) {
            map.removeLayer(clickMarker);
            clickMarker = null;
        }
        if (nearestStationPopup) {
            map.closePopup(nearestStationPopup);
            nearestStationPopup = null;
        }
        setStatus(`Đã chọn ga đến: ${station.name}`);
    }
}

/**
 * Khởi tạo click handler khi bản đồ sẵn sàng
 */
function initMapClickHandler() {
    if (typeof map !== "undefined" && map) {
        map.on("click", handleMapClick);
    }
}

// Gọi khi script được load
initMapClickHandler();
