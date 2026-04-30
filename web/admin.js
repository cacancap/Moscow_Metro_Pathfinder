const adminState = {
    routeStations: [],
    stationCatalog: [],
    edgeList: [],
    routeStopNameById: new Map(),
    selectedNodes: new Set(),
    selectedEdges: new Set(),
};

function initAdminPage() {
    if (!document.querySelector(".admin-page")) {
        return;
    }

    const blockedConfig = getBlockedConfig();
    adminState.selectedNodes = new Set(blockedConfig.blockedNodes);
    adminState.selectedEdges = new Set(blockedConfig.blockedEdges);

    bindAdminEvents();
    loadAdminData();
}

function bindAdminEvents() {
    document.getElementById("adminStationSearch").addEventListener("input", renderStationResults);
    document.getElementById("adminEdgeSearch").addEventListener("input", renderEdgeResults);
    document.getElementById("saveClosuresBtn").addEventListener("click", saveClosures);
    document.getElementById("refreshAdminBtn").addEventListener("click", loadAdminData);
    document.getElementById("clearStationsBtn").addEventListener("click", () => {
        adminState.selectedNodes.clear();
        refreshAdminSelections();
        setAdminStatus("Đã xóa toàn bộ ga bị khóa khỏi danh sách chờ lưu.");
    });
    document.getElementById("clearEdgesBtn").addEventListener("click", () => {
        adminState.selectedEdges.clear();
        refreshAdminSelections();
        setAdminStatus("Đã xóa toàn bộ cạnh bị khóa khỏi danh sách chờ lưu.");
    });
}

async function loadAdminData() {
    setAdminStatus("Đang tải dữ liệu quản trị...");

    try {
        const [routeStations, stationCatalog, edgeList] = await Promise.all([
            fetchJson(API_ENDPOINTS.routeStations),
            fetchJson(API_ENDPOINTS.stationCatalog),
            fetchJson(API_ENDPOINTS.edgeList),
        ]);

        adminState.routeStations = routeStations;
        adminState.stationCatalog = stationCatalog;
        adminState.edgeList = edgeList;
        adminState.routeStopNameById = new Map(routeStations.map((station) => [station.id, station.name]));

        refreshAdminSelections();
        renderStationResults();
        renderEdgeResults();
        setAdminStatus("Dữ liệu đã tải xong. Thay đổi sẽ có hiệu lực ở trang bản đồ sau khi lưu.");
    } catch (error) {
        setAdminStatus(`Không tải được dữ liệu quản trị: ${error.message}`);
    }
}

function renderStationResults() {
    const query = document.getElementById("adminStationSearch").value.trim().toLowerCase();
    const container = document.getElementById("adminStationResults");
    container.innerHTML = "";

    const results = adminState.routeStations
        .filter((station) => !query || station.name.toLowerCase().includes(query))
        .slice(0, 12);

    for (const station of results) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "result-item";
        item.innerHTML = `
            <strong>${station.name}</strong>
            <span>${station.id}</span>
        `;
        item.addEventListener("click", () => {
            adminState.selectedNodes.add(station.id);
            refreshAdminSelections();
            setAdminStatus(`Đã thêm ga ${station.name} vào danh sách block.`);
        });
        container.appendChild(item);
    }
}

function renderEdgeResults() {
    const query = document.getElementById("adminEdgeSearch").value.trim().toLowerCase();
    const container = document.getElementById("adminEdgeResults");
    container.innerHTML = "";

    const results = adminState.edgeList
        .map((edge) => ({
            edge,
            label: [
                edge.edge_id,
                edge.line_id,
                edge.edge_type,
                adminState.routeStopNameById.get(edge.source_id) || edge.source_id,
                adminState.routeStopNameById.get(edge.dest_id) || edge.dest_id,
            ].join(" "),
        }))
        .filter((item) => !query || item.label.toLowerCase().includes(query))
        .slice(0, 12);

    for (const item of results) {
        const edge = item.edge;
        const sourceName = adminState.routeStopNameById.get(edge.source_id) || edge.source_id;
        const targetName = adminState.routeStopNameById.get(edge.dest_id) || edge.dest_id;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-item";
        button.innerHTML = `
            <strong>${edge.edge_id}</strong>
            <span>${sourceName} -> ${targetName} | line ${edge.line_id || "?"}</span>
        `;
        button.addEventListener("click", () => {
            adminState.selectedEdges.add(edge.edge_id);
            refreshAdminSelections();
            setAdminStatus(`Đã thêm cạnh ${edge.edge_id} vào danh sách block.`);
        });
        container.appendChild(button);
    }
}

function refreshAdminSelections() {
    renderChipList(
        document.getElementById("blockedStationsList"),
        [...adminState.selectedNodes].map((stopId) => ({
            id: stopId,
            label: adminState.routeStopNameById.get(stopId) || stopId,
        })),
        (stopId) => {
            adminState.selectedNodes.delete(stopId);
            refreshAdminSelections();
        }
    );

    renderChipList(
        document.getElementById("blockedEdgesList"),
        [...adminState.selectedEdges].map((edgeId) => ({
            id: edgeId,
            label: edgeId,
        })),
        (edgeId) => {
            adminState.selectedEdges.delete(edgeId);
            refreshAdminSelections();
        }
    );

    document.getElementById("adminStationCount").innerText = String(adminState.routeStations.length);
    document.getElementById("adminEdgeCount").innerText = String(adminState.edgeList.length);
    document.getElementById("adminBlockedStations").innerText = String(adminState.selectedNodes.size);
    document.getElementById("adminBlockedEdges").innerText = String(adminState.selectedEdges.size);
}

function renderChipList(container, items, onRemove) {
    container.innerHTML = "";

    if (items.length === 0) {
        container.innerHTML = `<span class="muted-text">Chưa có phần tử nào.</span>`;
        return;
    }

    for (const item of items) {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "chip chip-action";
        chip.innerHTML = `<span>${item.label}</span><strong>×</strong>`;
        chip.addEventListener("click", () => onRemove(item.id));
        container.appendChild(chip);
    }
}

function saveClosures() {
    saveBlockedConfig({
        blockedNodes: dedupe([...adminState.selectedNodes]),
        blockedEdges: dedupe([...adminState.selectedEdges]),
    });
    setAdminStatus("Đã lưu cấu hình rerouting vào trình duyệt. Trang bản đồ sẽ dùng ngay cấu hình này.");
}

function setAdminStatus(message) {
    document.getElementById("adminStatusText").innerText = message;
}

document.addEventListener("DOMContentLoaded", initAdminPage);
