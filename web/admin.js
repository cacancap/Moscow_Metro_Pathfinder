const adminState = {
    routeStations: [],
    stationCatalog: [],
    edgeList: [],
    networkSummary: null,
    routeStopIds: new Set(),
    routeStopNameById: new Map(),
    stationNameByStopId: new Map(),
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
        setAdminStatus("Đã xóa ga.");
    });
    document.getElementById("clearEdgesBtn").addEventListener("click", () => {
        adminState.selectedEdges.clear();
        refreshAdminSelections();
        setAdminStatus("Đã xóa cạnh.");
    });
}

async function loadAdminData() {
    setAdminStatus("Đang tải...");

    try {
        const [summary, routeStations, stationCatalog, edgeList] = await Promise.all([
            fetchJson(API_ENDPOINTS.networkSummary),
            fetchJson(API_ENDPOINTS.routeStations),
            fetchJson(API_ENDPOINTS.stationCatalog),
            fetchJson(API_ENDPOINTS.edgeList),
        ]);

        adminState.networkSummary = summary;
        adminState.routeStations = routeStations;
        adminState.stationCatalog = stationCatalog;
        adminState.edgeList = edgeList;
        adminState.routeStopIds = new Set(routeStations.map((station) => station.id));
        adminState.routeStopNameById = new Map(routeStations.map((station) => [station.id, station.name]));
        adminState.stationNameByStopId = buildStationNameByStopId(stationCatalog);

        refreshAdminSelections();
        renderStationResults();
        renderEdgeResults();
        setAdminStatus("Sẵn sàng.");
    } catch (error) {
        setAdminStatus(`Lỗi tải: ${error.message}`, true);
    }
}

function renderStationResults() {
    const query = document.getElementById("adminStationSearch").value.trim().toLowerCase();
    const container = document.getElementById("adminStationResults");
    container.innerHTML = "";

    const results = adminState.stationCatalog
        .map((station) => ({
            ...station,
            validStops: Array.isArray(station.stops)
                ? station.stops.filter((stopId) => adminState.routeStopIds.has(stopId))
                : [],
            searchText: [
                station.name,
                station.name_en,
                Array.isArray(station.line_id) ? station.line_id.join(" ") : station.line_id,
            ].join(" ").toLowerCase(),
        }))
        .filter((station) => station.validStops.length > 0)
        .filter((station) => !query || station.searchText.includes(query))
        .slice(0, 12);

    if (results.length === 0) {
        container.innerHTML = '<div class="empty-state">Không tìm thấy ga phù hợp.</div>';
        return;
    }

    for (const station of results) {
        const item = document.createElement("button");
        item.type = "button";
        item.className = "result-item";
        const lineId = Array.isArray(station.line_id) ? station.line_id.join(", ") : station.line_id;
        item.innerHTML = `
            <strong>${station.name}</strong>
            <span>${station.name_en || "Không có tên tiếng Anh"} | line ${lineId || "?"} | ${station.validStops.length} stop/node</span>
        `;
        item.addEventListener("click", () => {
            for (const stopId of station.validStops) {
                adminState.selectedNodes.add(stopId);
            }
            refreshAdminSelections();
            setAdminStatus(`Đã thêm ${station.name}.`);
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
                adminState.stationNameByStopId.get(edge.source_id) || adminState.routeStopNameById.get(edge.source_id) || edge.source_id,
                adminState.stationNameByStopId.get(edge.dest_id) || adminState.routeStopNameById.get(edge.dest_id) || edge.dest_id,
            ].join(" "),
        }))
        .filter((item) => !query || item.label.toLowerCase().includes(query))
        .slice(0, 12);

    if (results.length === 0) {
        container.innerHTML = '<div class="empty-state">Không tìm thấy edge phù hợp.</div>';
        return;
    }

    for (const item of results) {
        const edge = item.edge;
        const sourceName = adminState.stationNameByStopId.get(edge.source_id) || adminState.routeStopNameById.get(edge.source_id) || edge.source_id;
        const targetName = adminState.stationNameByStopId.get(edge.dest_id) || adminState.routeStopNameById.get(edge.dest_id) || edge.dest_id;

        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-item";
        button.innerHTML = `
            <strong>${edge.edge_id}</strong>
            <span>${sourceName} → ${targetName} | line ${edge.line_id || "?"}</span>
        `;
        button.addEventListener("click", () => {
            adminState.selectedEdges.add(edge.edge_id);
            refreshAdminSelections();
            setAdminStatus(`Đã thêm ${edge.edge_id}.`);
        });
        container.appendChild(button);
    }
}

function refreshAdminSelections() {
    renderChipList(
        document.getElementById("blockedStationsList"),
        [...adminState.selectedNodes].map((stopId) => ({
            id: stopId,
            label: adminState.stationNameByStopId.get(stopId) || adminState.routeStopNameById.get(stopId) || stopId,
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

    document.getElementById("adminStationCount").innerText = formatNumber(adminState.routeStations.length);
    document.getElementById("adminEdgeCount").innerText = formatNumber(adminState.edgeList.length);
    document.getElementById("adminBlockedStations").innerText = String(adminState.selectedNodes.size);
    document.getElementById("adminBlockedEdges").innerText = String(adminState.selectedEdges.size);
    document.getElementById("adminStationSelectionCount").innerText = `${adminState.selectedNodes.size} mục`;
    document.getElementById("adminEdgeSelectionCount").innerText = `${adminState.selectedEdges.size} mục`;
    const dataSourceNode = document.getElementById("adminDataSource");
    if (adminState.networkSummary && dataSourceNode) {
        dataSourceNode.innerText = "data/processed/outputs";
    }
}

function buildStationNameByStopId(stationCatalog) {
    const mapping = new Map();

    for (const station of stationCatalog) {
        const label = station.name_en ? `${station.name} / ${station.name_en}` : station.name;
        for (const stopId of station.stops || []) {
            mapping.set(stopId, label);
        }
    }

    return mapping;
}

function renderChipList(container, items, onRemove) {
    container.innerHTML = "";

    if (items.length === 0) {
        container.innerHTML = '<span class="muted-text">Chưa có phần tử nào.</span>';
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
    setAdminStatus("Đã lưu.");
}

function setAdminStatus(message, isError = false) {
    const node = document.getElementById("adminStatusText");
    node.innerText = message;
    node.classList.toggle("is-error", isError);
}

document.addEventListener("DOMContentLoaded", initAdminPage);
