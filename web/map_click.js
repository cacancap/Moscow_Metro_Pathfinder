/**
 * Map Click Handler — Tìm ga gần nhất từ điểm click
 */

let clickMarker = null;
let nearestStationMarker = null;
let nearestStationPopup = null;
let clickSearchMode = false;
let mapClickHandlerAttached = false;
const STATION_CLICK_THRESHOLD_METERS = 30;

/**
 * Xử lý khi người dùng click trên bản đồ
 */
function handleMapClick(e) {
    if (!clickSearchMode) {
        return;
    }

    const { lat, lng } = e.latlng;
    findNearestStation(lat, lng);
}

/**
 * Bật/tắt chế độ click tìm ga gần nhất
 */
function toggleClickStationMode() {
    clickSearchMode = !clickSearchMode;
    const button = document.getElementById("clickStationModeBtn");
    if (!button) {
        return;
    }

    if (clickSearchMode) {
        button.classList.remove("btn-ghost");
        button.classList.add("btn-primary");
        button.innerText = "Chế độ click tìm ga: BẬT";
        setStatus("Chế độ click tìm ga gần nhất đã bật. Hãy click vào bản đồ.");
    } else {
        button.classList.remove("btn-primary");
        button.classList.add("btn-ghost");
        button.innerText = "Click tìm ga gần nhất";
        setStatus("Chế độ click tìm ga gần nhất đã tắt.");
        clearNearestSearchMarkers();
    }
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
        
        clearNearestSearchMarkers();
        
        const isStationClick = station.distance_meters <= STATION_CLICK_THRESHOLD_METERS;
        if (!isStationClick) {
            clickMarker = L.marker([lat, lon]).addTo(state.map);
            clickMarker.bindPopup(
                `<div style="font-size:0.85rem; text-align:center;">
                    <div><strong>Điểm Click</strong></div>
                    <div>Lat: ${lat.toFixed(4)}</div>
                    <div>Lon: ${lon.toFixed(4)}</div>
                    <div style="margin-top: 6px; font-size: 0.75rem; color: #666;">Ga gần nhất đang hiển thị phía dưới.</div>
                </div>`
            ).openPopup();
        }
        
        nearestStationMarker = L.marker([station.lat, station.lon]).addTo(state.map);
        
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
        
        nearestStationMarker.bindPopup(popupContent).openPopup();
        nearestStationPopup = nearestStationMarker.getPopup();
    } catch (error) {
        console.error("Error finding nearest station:", error);
        if (clickMarker && clickMarker.getPopup) {
            const popup = clickMarker.getPopup();
            if (popup) {
                popup.setContent(
                    `<div style="font-size:0.85rem; text-align:center; color: red;">
                        <div>Lỗi: ${error.message}</div>
                    </div>`
                );
            }
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

function clearNearestSearchMarkers() {
    if (nearestStationPopup) {
        if (state.map) {
            state.map.closePopup(nearestStationPopup);
        }
        nearestStationPopup = null;
    }
    if (nearestStationMarker) {
        if (state.map) {
            state.map.removeLayer(nearestStationMarker);
        }
        nearestStationMarker = null;
    }
    if (clickMarker) {
        if (state.map) {
            state.map.removeLayer(clickMarker);
        }
        clickMarker = null;
    }
}

/**
 * Đặt ga gần nhất làm điểm khởi đầu
 */
function setAsStart(stationId) {
    const station = state.stationById.get(stationId);
    if (station) {
        setStartStation(stationId);
        closeStationPanel();
        clearNearestSearchMarkers();
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
        clearNearestSearchMarkers();
        updateSelectionSummary();
        setStatus(`Đã chọn ga đến: ${station.name}`);
    }
}

/**
 * Khởi tạo click handler khi bản đồ sẵn sàng
 */
function attachMapClickHandler() {
    if (!state.map || mapClickHandlerAttached) {
        return;
    }

    state.map.on("click", handleMapClick);
    mapClickHandlerAttached = true;
}

function initMapClickHandler() {
    if (state.map) {
        attachMapClickHandler();
        return;
    }

    document.addEventListener("DOMContentLoaded", () => {
        attachMapClickHandler();
    });
}
