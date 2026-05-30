const moscowCenter = [55.751244, 37.618423];

const state = {
    map: null,
    stationMarkersVisible: true,
    routeLayer: null,
    stationLayer: null,
    bombLayer: null,
    bombPreviewCircle: null,
    bombMode: false,
    bombPendingLat: null,
    bombPendingLng: null,
    highlightedMarker: null,
    stationCatalog: [],
    routeStops: [],
    routeStopIds: new Set(),
    routeStopNameById: new Map(),
    stationOptions: [],
    stationById: new Map(),
    stationByRouteStop: new Map(),
    edgeById: new Map(),
    adjacency: new Map(),
    networkSummary: null,
    reachableEndIds: null,
    panelCollapsed: false,
};

const bombCircles = new Map();

function initMapPage() {
    if (!document.getElementById("map")) {
        return;
    }

    buildMap();
    if (typeof initMapClickHandler === "function") {
        initMapClickHandler();
    }
    bindUiEvents();
    loadAppData();
    renderRouteHistory();
    updateRouteSummary();
    updateStationToggleButton();
    initBombs();
}

function buildMap() {
    state.map = L.map("map", { zoomControl: false, preferCanvas: true }).setView(moscowCenter, 11);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
        maxZoom: 19,
    }).addTo(state.map);

    L.control.zoom({ position: "bottomright" }).addTo(state.map);
    state.routeLayer = L.layerGroup().addTo(state.map);
    state.stationLayer = L.layerGroup().addTo(state.map);
    state.bombLayer = L.layerGroup().addTo(state.map);
}

function bindUiEvents() {
    document.getElementById("stationSearch").addEventListener("input", onSearchInput);
    document.getElementById("togglePanelBtn").addEventListener("click", togglePanel);
    document.getElementById("mobileDrawerHandle").addEventListener("click", togglePanel);
    document.getElementById("startStation").addEventListener("change", onStartStationChange);
    document.getElementById("endStation").addEventListener("change", updateSelectionSummary);
    document.getElementById("bombModeBtn").addEventListener("click", toggleBombMode);
    document.getElementById("cancelBombBtn").addEventListener("click", cancelBomb);
    document.getElementById("confirmBombBtn").addEventListener("click", confirmBomb);
    document.getElementById("bombRadiusInput").addEventListener("keydown", onBombRadiusKey);
    document.getElementById("bombRadiusInput").addEventListener("input", previewBombCircle);
}

async function loadAppData() {
    setStatus("Đang tải...");

    try {
        const [summary, stationCatalog, routeStops, edgeList] = await Promise.all([
            fetchJson(API_ENDPOINTS.networkSummary),
            fetchJson(API_ENDPOINTS.stationCatalog),
            fetchJson(API_ENDPOINTS.routeStations),
            fetchJson(API_ENDPOINTS.edgeList),
        ]);

        state.networkSummary = summary;
        state.stationCatalog = stationCatalog;
        state.routeStops = routeStops;
        state.routeStopIds = new Set(routeStops.map((station) => station.id));
        state.routeStopNameById = new Map(routeStops.map((station) => [station.id, station.name]));
        state.edgeById = new Map(edgeList.map((edge) => [edge.edge_id, edge]));
        state.adjacency = buildAdjacency(edgeList);

        buildStationOptionIndex();
        populateStationSelects();
        renderStationMarkers();
        updateStationBlockedVisuals();
        renderNetworkSummary();
        renderClosureSummary();
        updateSelectionSummary();
        setStatus("Sẵn sàng.");
    } catch (error) {
        setStatus(`Lỗi tải: ${error.message}`, true);
    }
}

function buildStationOptionIndex() {
    const stationOptions = [];
    state.stationById.clear();
    state.stationByRouteStop.clear();

    for (const station of state.stationCatalog) {
        const validStops = Array.isArray(station.stops)
            ? station.stops.filter((stopId) => state.routeStopIds.has(stopId))
            : [];

        if (validStops.length === 0) {
            continue;
        }

        const option = {
            stationId: station.id,
            routeStopId: validStops[0],
            name: station.name || "Unknown",
            nameEn: station.name_en || "",
            colour: station.colour || "gray",
            lineId: Array.isArray(station.line_id) ? station.line_id.join(", ") : (station.line_id || "?"),
            geometry: station.geometry || [],
            stops: validStops,
        };

        stationOptions.push(option);
        state.stationById.set(option.stationId, option);
        for (const stopId of validStops) {
            state.stationByRouteStop.set(stopId, option);
        }
    }

    stationOptions.sort((left, right) => left.name.localeCompare(right.name, "ru"));
    state.stationOptions = stationOptions;
}

function populateStationSelects() {
    const startSelect = document.getElementById("startStation");
    const endSelect = document.getElementById("endStation");
    const currentStart = startSelect.value;
    const currentEnd = endSelect.value;

    startSelect.innerHTML = "";
    endSelect.innerHTML = "";

    startSelect.add(new Option("Chọn ga đi", ""));
    endSelect.add(new Option("Chọn ga đến", ""));

    let reachableCount = 0;

    for (const station of state.stationOptions) {
        const label = `[${station.lineId}] ${station.name}${station.nameEn ? ` / ${station.nameEn}` : ""}`;
        startSelect.add(new Option(label, station.stationId));
        if (!state.reachableEndIds || state.reachableEndIds.has(station.stationId)) {
            endSelect.add(new Option(label, station.stationId));
            if (state.reachableEndIds) {
                reachableCount += 1;
            }
        }
    }

    startSelect.value = currentStart && state.stationById.has(currentStart) ? currentStart : "";
    endSelect.value = currentEnd && [...endSelect.options].some((option) => option.value === currentEnd) ? currentEnd : "";

    const reachableLabel = document.getElementById("reachableCountValue");
    if (!state.reachableEndIds) {
        reachableLabel.innerText = "Chưa lọc";
    } else {
        reachableLabel.innerText = `${Math.max(reachableCount - 1, 0)} ga đích`;
    }
}

function renderStationMarkers() {
    state.stationLayer.clearLayers();

    for (const station of state.stationOptions) {
        const [lon, lat] = station.geometry;
        if (!Number.isFinite(lon) || !Number.isFinite(lat)) {
            continue;
        }

        const color = resolveLineColor(station.colour);
        const marker = L.circleMarker([lat, lon], {
            radius: 9,
            color,
            weight: 2.5,
            fillColor: color,
            fillOpacity: 0.98,
            pane: 'markerPane'
        });

        marker.on("click", () => openStationPanel(station));
        marker.bindTooltip(
            station.nameEn ? `${station.name} / ${station.nameEn}` : station.name,
            { direction: "top", opacity: 0.95 }
        );
        marker.addTo(state.stationLayer);
        station.marker = marker;
    }

    updateVisibleStationCount();
}

function updateStationBlockedVisuals() {
    const blockedNodes = new Set(getEffectiveBlockedConfig().blockedNodes);

    for (const station of state.stationOptions) {
        if (!station.marker) {
            continue;
        }

        const blocked = isStationFullyBlocked(station, blockedNodes);
        station.marker.setStyle({
            radius: blocked ? 6 : 5,
            color: blocked ? "#9f2440" : resolveLineColor(station.colour),
            fillColor: blocked ? "#9f2440" : resolveLineColor(station.colour),
            fillOpacity: blocked ? 0.38 : 0.92,
            opacity: blocked ? 0.8 : 1,
            weight: blocked ? 2.2 : 1.5,
        });
    }
}

function isStationFullyBlocked(station, blockedNodes = new Set(getEffectiveBlockedConfig().blockedNodes)) {
    return station.stops.length > 0 && station.stops.every((stopId) => blockedNodes.has(stopId));
}

function renderNetworkSummary() {
    const summary = state.networkSummary || {};
    const lineCount = summary.lines ? Object.keys(summary.lines).length : "--";

    document.getElementById("summaryStationCount").innerText = formatNumber(summary.station_nodes);
    document.getElementById("summaryEdgeCount").innerText = formatNumber(summary.edges);
    document.getElementById("summaryLineCount").innerText = formatNumber(lineCount);

}

function onSearchInput(event) {
    const query = event.target.value.trim().toLowerCase();
    const resultsContainer = document.getElementById("searchResults");

    if (!query) {
        resultsContainer.innerHTML = "";
        return;
    }

    const matches = state.stationOptions.filter((station) => {
        const haystack = `${station.name} ${station.nameEn} ${station.lineId}`.toLowerCase();
        return haystack.includes(query);
    }).slice(0, 8);

    resultsContainer.innerHTML = "";

    if (matches.length === 0) {
        resultsContainer.innerHTML = '<div class="empty-state">Không tìm thấy ga phù hợp.</div>';
        return;
    }

    for (const station of matches) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-item";
        const color = resolveLineColor(station.colour);
        button.innerHTML = `
            <div class="line-dot" style="background:${color}"></div>
            <div class="result-item-text">
                <strong>${station.name}</strong>
                <span>${station.nameEn ? station.nameEn + " · " : ""}tuyến ${station.lineId}</span>
            </div>
        `;
        button.addEventListener("click", () => {
            focusStation(station);
            openStationPanel(station);
            resultsContainer.innerHTML = "";
            document.getElementById("stationSearch").value = station.name;
        });
        resultsContainer.appendChild(button);
    }
}

function focusStation(station) {
    const [lon, lat] = station.geometry;
    state.map.flyTo([lat, lon], 13, { duration: 0.8 });

    if (state.highlightedMarker) {
        state.highlightedMarker.setStyle({ radius: 5, weight: 1.5 });
    }

    if (station.marker) {
        station.marker.setStyle({ radius: 8, weight: 2.5 });
        state.highlightedMarker = station.marker;
    }
}

function openStationPanel(station) {
    const panel = document.getElementById("stationInfo");
    const closeStationButton = document.getElementById("closeStationBtn");
    panel.classList.remove("hidden");

    document.getElementById("stationName").innerText = station.name;
    document.getElementById("stationNameEn").innerText = station.nameEn || "-";
    document.getElementById("stationLine").innerText = station.lineId || "-";
    document.getElementById("stationStops").innerText = station.stops.join(", ");
    document.getElementById("stationCoords").innerText = `${station.geometry[1].toFixed(5)}, ${station.geometry[0].toFixed(5)}`;

    document.getElementById("useAsStartBtn").onclick = () => {
        setStartStation(station.stationId);
    };
    document.getElementById("useAsEndBtn").onclick = () => {
        document.getElementById("endStation").value = station.stationId;
        updateSelectionSummary();
        closeStationPanel();
    };

    if (localStorage.getItem(STORAGE_KEYS.role) === "admin") {
        closeStationButton.classList.remove("hidden");
        closeStationButton.innerText = isStationFullyBlocked(station) ? "Ga đã đóng" : "Đóng ga";
        closeStationButton.disabled = isStationFullyBlocked(station);
        closeStationButton.onclick = () => closeStationFromPanel(station);
    } else {
        closeStationButton.classList.add("hidden");
        closeStationButton.onclick = null;
    }
}

function closeStationPanel() {
    document.getElementById("stationInfo").classList.add("hidden");
}

function closeStationFromPanel(station) {
    const blockedConfig = getBlockedConfig();
    const blockedNodes = dedupe([...blockedConfig.blockedNodes, ...station.stops]);

    saveBlockedConfig({
        blockedNodes,
        blockedEdges: dedupe(blockedConfig.blockedEdges),
    });

    renderClosureSummary();
    updateStationBlockedVisuals();

    const startStationId = document.getElementById("startStation").value;
    if (startStationId) {
        state.reachableEndIds = getReachableDestinations(startStationId);
        populateStationSelects();
    }
    updateSelectionSummary();

    const closeStationButton = document.getElementById("closeStationBtn");
    closeStationButton.innerText = "Ga đã đóng";
    closeStationButton.disabled = true;

    setStatus(`Đã đóng ${station.name}.`);
}

async function findPath() {
    const startStationId = document.getElementById("startStation").value;
    const endStationId = document.getElementById("endStation").value;
    const algorithm = document.getElementById("algorithm").value;
    const blockedConfig = getEffectiveBlockedConfig();
    const findButton = document.getElementById("findPathBtn");

    if (!startStationId || !endStationId) {
        setStatus("Thiếu ga đi/đến.", true);
        return;
    }

    if (startStationId === endStationId) {
        setStatus("Ga đi trùng ga đến.", true);
        return;
    }

    const startStation = state.stationById.get(startStationId);
    const endStation = state.stationById.get(endStationId);

    if (!startStation || !endStation) {
        setStatus("Ga không hợp lệ.", true);
        return;
    }

    const blockedNodes = new Set(blockedConfig.blockedNodes);
    const startCandidates = startStation.stops.filter((stopId) => !blockedNodes.has(stopId));
    const endCandidates = endStation.stops.filter((stopId) => !blockedNodes.has(stopId));

    if (startCandidates.length === 0 || endCandidates.length === 0) {
        setStatus("Ga đang bị đóng.", true);
        return;
    }

    setStatus(`Đang tìm ${startStation.name} → ${endStation.name}...`);
    setMetricValues("--", "--", "--");
    findButton.disabled = true;
    findButton.innerText = "Đang tìm...";

    try {
        const result = await findBestPath(startCandidates, endCandidates, blockedConfig, algorithm);
        renderPath(result, algorithm);
    } catch (error) {
        clearRouteLayer();
        setStatus(`Không tìm được: ${error.message}`, true);
        showToast(`Không tìm được đường! ${error.message}`, true);
    } finally {
        findButton.disabled = false;
        findButton.innerText = "Tìm đường";
    }
}

async function findBestPath(startCandidates, endCandidates, blockedConfig, algorithm) {
    const attempts = [];

    for (const startId of startCandidates) {
        for (const endId of endCandidates) {
            if (startId !== endId) {
                attempts.push({ startId, endId });
            }
        }
    }

    const errors = [];
    let bestResult = null;

    for (const attempt of attempts) {
        try {
            const payload = await fetchJson(API_ENDPOINTS.findPath, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    start_id: attempt.startId,
                    target_id: attempt.endId,
                    algorithm: algorithm || "astar",
                    blocked_edges: blockedConfig.blockedEdges,
                    blocked_nodes: blockedConfig.blockedNodes,
                }),
            });

            const result = payload.result;
            if (!bestResult || Number(result.total_distance_meters) < Number(bestResult.total_distance_meters)) {
                bestResult = result;
            }
        } catch (error) {
            errors.push(error.message);
        }
    }

    if (!bestResult) {
        throw new Error(errors[0] || "Không tìm được đường.");
    }

    return bestResult;
}

function renderPath(result, algorithm) {
    clearRouteLayer();

    const latLngs = [];
    for (const edgeId of result.path_edges || []) {
        const edge = state.edgeById.get(edgeId);
        if (!edge || !Array.isArray(edge.geometry)) {
            continue;
        }

        const segment = edge.geometry.map(([lon, lat]) => [lat, lon]);
        if (latLngs.length > 0 && segment.length > 0) {
            const [prevLat, prevLng] = latLngs[latLngs.length - 1];
            const [nextLat, nextLng] = segment[0];
            if (prevLat === nextLat && prevLng === nextLng) {
                segment.shift();
            }
        }
        latLngs.push(...segment);
    }

    if (latLngs.length > 1) {
        const polyline = L.polyline(latLngs, {
            color: "#f97316",
            weight: 6,
            opacity: 0.92,
            lineJoin: "round",
        }).addTo(state.routeLayer);

        const startMarker = L.circleMarker(latLngs[0], {
            radius: 8,
            color: "#fde68a",
            weight: 2,
            fillColor: "#fde68a",
            fillOpacity: 1,
            pane: 'markerPane'
        }).addTo(state.routeLayer);

        const endMarker = L.circleMarker(latLngs[latLngs.length - 1], {
            radius: 8,
            color: "#6ee7b7",
            weight: 2,
            fillColor: "#6ee7b7",
            fillOpacity: 1,
            pane: 'markerPane'
        }).addTo(state.routeLayer);

        startMarker.bindTooltip("Start", { permanent: false });
        endMarker.bindTooltip("End", { permanent: false });
        
        state.map.fitBounds(polyline.getBounds(), { padding: [64, 64] });
    }

    const stationNames = extractRouteStationNames(result.path_nodes || []);
    const blockedConfig = getBlockedConfig();
    const startStation = state.stationByRouteStop.get(result.path_nodes?.[0]);
    const endStation = state.stationByRouteStop.get(result.path_nodes?.[result.path_nodes.length - 1]);
    const startName = startStation?.name || result.origin || "Unknown";
    const endName = endStation?.name || result.destination || "Unknown";

    setMetricValues(formatDistance(result.total_distance_meters), String(result.node_count || 0), formatElapsed(result.elapsed_ms));
    setStatus(`
        <strong>${startName}</strong> đến <strong>${endName}</strong><br>
        Quãng đường: <strong>${formatDistance(result.total_distance_meters)}</strong><br>
        Thời gian tính: <strong>${formatElapsed(result.elapsed_ms)}</strong><br>
        Điểm: <strong>${result.node_count}</strong><br>
        Ga đóng: <strong>${blockedConfig.blockedNodes.length}</strong>,
        cạnh chặn: <strong>${blockedConfig.blockedEdges.length}</strong>
    `);

    document.getElementById("routeSummaryTitle").innerText = `${startName} → ${endName}`;
    document.getElementById("routeSummaryMeta").innerText = `${stationNames.length} ga · ${formatDistance(result.total_distance_meters)}`;

    renderRouteStations(stationNames);
    saveRouteHistory({
        start: startName,
        end: endName,
        algorithm,
        cost: result.total_distance_meters,
        nodeCount: result.node_count,
        timestamp: new Date().toISOString(),
    });
    renderRouteHistory();
}

function extractRouteStationNames(pathNodes) {
    const stations = [];
    let previousName = null;

    for (const nodeId of pathNodes) {
        const station = state.stationByRouteStop.get(nodeId);
        const name = station?.name || state.routeStopNameById.get(nodeId) || null;
        if (!name || name === previousName) {
            continue;
        }
        stations.push({ name, colour: station?.colour || "" });
        previousName = name;
    }

    return stations;
}

function renderRouteStations(stations) {
    const container = document.getElementById("routeStationsList");
    container.innerHTML = "";

    if (stations.length === 0) {
        container.innerHTML = '<div class="empty-state">Không có dữ liệu ga.</div>';
        return;
    }

    for (const [index, { name, colour }] of stations.entries()) {
        const item = document.createElement("div");
        item.className = "route-station-item";
        const color = resolveLineColor(colour);
        const dot = colour
            ? `<div class="line-dot" style="background:${color};flex-shrink:0"></div>`
            : "";
        item.innerHTML = `<span>${String(index + 1).padStart(2, "0")}</span>${dot}<strong>${name}</strong>`;
        container.appendChild(item);
    }
}

function renderClosureSummary() {
    const container = document.getElementById("closureSummary");
    const blockedConfig = getEffectiveBlockedConfig();
    const bombs = getBombs();
    const isAdmin = localStorage.getItem("metro_user_role") === "admin";

    const blockedStationNames = blockedConfig.blockedNodes
        .map((stopId) => state.stationByRouteStop.get(stopId)?.name || state.routeStopNameById.get(stopId) || stopId)
        .slice(0, 4);

    const blockedEdgeNames = blockedConfig.blockedEdges.slice(0, 4);

    let bombHtml = "";
    if (bombs.length > 0) {
        const cardsHtml = bombs.map((bomb, index) => {
            const dt = new Date(bomb.timestamp);
            const timeStr = dt.toLocaleString("vi-VN", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
            const latStr = `${Math.abs(bomb.lat).toFixed(4)}°${bomb.lat >= 0 ? "N" : "S"}`;
            const lngStr = `${Math.abs(bomb.lng).toFixed(4)}°${bomb.lng >= 0 ? "E" : "W"}`;
            return `
                <div class="bomb-card" data-bomb-id="${bomb.id}">
                    <div class="bomb-card-header">
                        <span class="bomb-card-title">💣 #${index + 1}</span>
                        <div class="bomb-card-actions">
                            <button class="btn btn-ghost bomb-fly-btn" type="button" data-lat="${bomb.lat}" data-lng="${bomb.lng}" title="Tới vị trí">📍</button>
                            ${isAdmin ? `<button class="btn btn-danger bomb-remove-btn" type="button" data-bomb-id="${bomb.id}">Xóa</button>` : ""}
                        </div>
                    </div>
                    <div class="bomb-card-body">
                        <div class="bomb-stat-row"><span class="detail-label">Tọa độ</span><strong>${latStr}, ${lngStr}</strong></div>
                        <div class="bomb-stat-row"><span class="detail-label">Bán kính</span><strong>${bomb.radius} km</strong></div>
                        <div class="bomb-stat-row"><span class="detail-label">Phá hủy</span><strong>${bomb.affectedNodes.length} ga · ${bomb.affectedEdges.length} cạnh</strong></div>
                        <div class="bomb-stat-row"><span class="detail-label">Lúc</span><strong>${timeStr}</strong></div>
                    </div>
                </div>`;
        }).join("");

        bombHtml = `
            <div class="closure-line">
                <span>💣 Vụ nổ</span>
                <strong>${bombs.length}</strong>
                ${isAdmin ? `<button class="btn btn-ghost btn-xs closure-clear-bombs" type="button">Xóa tất cả</button>` : ""}
            </div>
            ${cardsHtml}`;
    }

    container.innerHTML = `
        ${bombHtml}
        <div class="closure-line">
            <span>Ga đang khóa</span>
            <strong>${blockedConfig.blockedNodes.length}</strong>
        </div>
        <div class="closure-chip-row">${blockedStationNames.map((item) => `<span class="chip chip-muted">${item}</span>`).join("") || '<span class="muted-text">Không có</span>'}</div>
        <div class="closure-line">
            <span>Cạnh đang khóa</span>
            <strong>${blockedConfig.blockedEdges.length}</strong>
        </div>
        <div class="closure-chip-row">${blockedEdgeNames.map((item) => `<span class="chip chip-muted">${item}</span>`).join("") || '<span class="muted-text">Không có</span>'}</div>
    `;

    container.querySelectorAll(".bomb-fly-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            state.map.flyTo([parseFloat(btn.dataset.lat), parseFloat(btn.dataset.lng)], 13, { duration: 0.9 });
        });
    });
    container.querySelectorAll(".bomb-remove-btn").forEach(btn => {
        btn.addEventListener("click", () => removeBomb(btn.dataset.bombId));
    });
    const clearAllBtn = container.querySelector(".closure-clear-bombs");
    if (clearAllBtn) clearAllBtn.addEventListener("click", clearAllBombs);
}

function renderRouteHistory() {
    const container = document.getElementById("historyList");
    const history = JSON.parse(localStorage.getItem(STORAGE_KEYS.routeHistory) || "[]");
    container.innerHTML = "";

    if (history.length === 0) {
        container.innerHTML = '<div class="empty-state">Chưa có lịch sử.</div>';
        return;
    }

    for (const item of history.slice(0, 6)) {
        const row = document.createElement("div");
        row.className = "history-item";
        row.innerHTML = `
            <div>
                <strong>${item.start} → ${item.end}</strong>
                <span>${item.algorithm?.toUpperCase() || "A*"} | ${formatDistance(item.cost)} | ${item.nodeCount || 0} điểm</span>
            </div>
            <time>${formatHistoryTime(item.timestamp)}</time>
        `;
        container.appendChild(row);
    }
}

function toggleStations() {
    state.stationMarkersVisible = !state.stationMarkersVisible;
    if (state.stationMarkersVisible) {
        state.stationLayer.addTo(state.map);
    } else {
        state.stationLayer.remove();
    }
    updateStationToggleButton();
    updateVisibleStationCount();
}

function centerMap() {
    state.map.flyTo(moscowCenter, 11, { duration: 0.8 });
}

function clearAll() {
    clearRouteLayer();
    setStartStation("");
    document.getElementById("endStation").value = "";
    document.getElementById("stationSearch").value = "";
    document.getElementById("searchResults").innerHTML = "";
    renderRouteStations([]);
    setMetricValues("--", "--", "--");
    setStatus("Đã xóa.");
    document.getElementById("routeSummaryTitle").innerText = "Chưa có lộ trình";
    document.getElementById("routeSummaryMeta").innerText = "Chọn ga đi và ga đến.";
    updateSelectionSummary();
}

function clearRouteLayer() {
    state.routeLayer.clearLayers();
}

function swapStations() {
    const startSelect = document.getElementById("startStation");
    const endSelect = document.getElementById("endStation");
    const temp = startSelect.value;
    setStartStation(endSelect.value);
    endSelect.value = temp;
    onStartStationChange();
}


function togglePanel() {
    state.panelCollapsed = !state.panelCollapsed;
    document.querySelector(".route-panel").classList.toggle("collapsed", state.panelCollapsed);
    document.getElementById("togglePanelBtn").innerText = state.panelCollapsed ? "+" : "−";
}

function setStatus(message, isError = false) {
    const stats = document.getElementById("stats");
    stats.innerHTML = message;
    stats.classList.toggle("is-error", isError);
}

function setMetricValues(distance, stations, elapsed) {
    document.getElementById("distanceValue").innerText = distance;
    document.getElementById("stationsValue").innerText = stations;
    document.getElementById("elapsedValue").innerText = elapsed;
}

function formatDistance(value) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return "--";
    }

    const meters = Number(value);
    if (meters >= 1000) {
        return `${(meters / 1000).toFixed(2)} km`;
    }
    return `${meters.toFixed(0)} m`;
}

function formatElapsed(value) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return "--";
    }
    return `${Number(value).toFixed(1)} ms`;
}

function resolveLineColor(rawColor) {
    const palette = {
        red: "#ff4d4d",
        blue: "#4f8cff",
        lightblue: "#62d0ff",
        green: "#34c47c",
        darkgreen: "#1d8f58",
        orange: "#ff9d42",
        yellow: "#f6d64a",
        violet: "#9d72ff",
        brown: "#9a684a",
        gray: "#9ea8ba",
        grey: "#9ea8ba",
        purple: "#8f7aff",
        pink: "#ff8eb6",
        lightpink: "#ffc2d8",
        teal: "#5bd4c8",
        lime: "#a7d84f",
    };

    const normalized = String(rawColor || "").toLowerCase();
    return palette[normalized] || normalized || "#7aa2ff";
}

function buildAdjacency(edgeList) {
    const adjacency = new Map();

    for (const edge of edgeList) {
        if (!adjacency.has(edge.source_id)) {
            adjacency.set(edge.source_id, []);
        }
        adjacency.get(edge.source_id).push({
            next: edge.dest_id,
            edgeId: edge.edge_id,
        });
    }

    return adjacency;
}

function onStartStationChange() {
    const startStationId = document.getElementById("startStation").value;
    state.reachableEndIds = startStationId ? getReachableDestinations(startStationId) : null;
    populateStationSelects();
    updateSelectionSummary();

    const endSelect = document.getElementById("endStation");
    if (startStationId && !endSelect.value) {
        setStatus(`${Math.max((state.reachableEndIds?.size || 1) - 1, 0)} ga đích khả dụng.`);
    }
}

function setStartStation(stationId) {
    document.getElementById("startStation").value = stationId;
    onStartStationChange();
}

function getReachableDestinations(startStationId) {
    const startStation = state.stationById.get(startStationId);
    if (!startStation) {
        return new Set();
    }

    const blockedConfig = getEffectiveBlockedConfig();
    const blockedNodes = new Set(blockedConfig.blockedNodes);
    const blockedEdges = new Set(blockedConfig.blockedEdges);
    const visited = new Set();
    const queue = [];

    for (const stopId of startStation.stops) {
        if (!blockedNodes.has(stopId)) {
            visited.add(stopId);
            queue.push(stopId);
        }
    }

    if (queue.length === 0) {
        return new Set();
    }

    while (queue.length > 0) {
        const current = queue.shift();
        const neighbors = state.adjacency.get(current) || [];

        for (const neighbor of neighbors) {
            if (blockedEdges.has(neighbor.edgeId) || blockedNodes.has(neighbor.next) || visited.has(neighbor.next)) {
                continue;
            }
            visited.add(neighbor.next);
            queue.push(neighbor.next);
        }
    }

    const reachableStations = new Set();
    for (const station of state.stationOptions) {
        if (station.stationId === startStationId) {
            continue;
        }
        if (station.stops.some((stopId) => visited.has(stopId))) {
            reachableStations.add(station.stationId);
        }
    }

    return reachableStations;
}

function updateSelectionSummary() {
    const startStationId = document.getElementById("startStation").value;
    const endStationId = document.getElementById("endStation").value;
    document.getElementById("activeStartValue").innerText = getStationLabelById(startStationId) || "Chưa chọn";
    document.getElementById("activeEndValue").innerText = getStationLabelById(endStationId) || "Chưa chọn";
}

function updateRouteSummary() {
    document.getElementById("routeSummaryTitle").innerText = "Chưa có lộ trình";
    document.getElementById("routeSummaryMeta").innerText = "Chọn ga đi và ga đến.";
}

function updateStationToggleButton() {
    const button = document.getElementById("toggleStationsBtn");
    button.innerText = state.stationMarkersVisible ? "Ẩn ga" : "Hiện ga";
}

function updateVisibleStationCount() {
    const count = state.stationMarkersVisible ? state.stationOptions.length : 0;
    document.getElementById("visibleStationCount").innerText = `${count} ga hiển thị`;
}

function getStationLabelById(stationId) {
    const station = state.stationById.get(stationId);
    if (!station) {
        return "";
    }
    return station.nameEn ? `${station.name} / ${station.nameEn}` : station.name;
}

function formatHistoryTime(timestamp) {
    if (!timestamp) {
        return "--";
    }

    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
        return "--";
    }

    return new Intl.DateTimeFormat("vi-VN", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

function showToast(message, isError = false) {
    const old = document.getElementById("appToast");
    if (old) old.remove();
    const el = document.createElement("div");
    el.id = "appToast";
    el.className = "toast" + (isError ? " toast-error" : "");
    el.textContent = message;
    document.body.appendChild(el);
    requestAnimationFrame(() => requestAnimationFrame(() => el.classList.add("toast-visible")));
    setTimeout(() => {
        el.classList.remove("toast-visible");
        setTimeout(() => el.remove(), 280);
    }, 3500);
}

// ===================== BOMB SYSTEM =====================

function initBombs() {
    redrawAllBombs();
    renderClosureSummary();
    if (localStorage.getItem("metro_user_role") === "admin") {
        document.getElementById("bombModeBtn").classList.remove("hidden");
    }
}

function toggleBombMode() {
    state.bombMode = !state.bombMode;
    const btn = document.getElementById("bombModeBtn");

    if (state.bombMode) {
        btn.classList.add("btn-bomb-active");
        btn.innerText = "🎯 Đang chọn tâm...";
        state.map.getContainer().style.cursor = "crosshair";
        state.map.on("click", onMapClickBomb);
    } else {
        btn.classList.remove("btn-bomb-active");
        btn.innerText = "💣 Thả bom";
        state.map.getContainer().style.cursor = "";
        state.map.off("click", onMapClickBomb);
        clearBombPreview();
        hideBombPopup();
    }
}

function onMapClickBomb(e) {
    state.bombPendingLat = e.latlng.lat;
    state.bombPendingLng = e.latlng.lng;
    showBombPopup(e.containerPoint);
}

function showBombPopup(containerPoint) {
    const popup = document.getElementById("bombPopup");
    const mapRect = document.getElementById("map").getBoundingClientRect();

    let x = mapRect.left + containerPoint.x + 14;
    let y = mapRect.top + containerPoint.y - 10;

    popup.classList.remove("hidden");

    const popupW = 230;
    const popupH = 180;
    if (x + popupW > window.innerWidth - 8) x = mapRect.left + containerPoint.x - popupW - 14;
    if (y + popupH > window.innerHeight - 8) y = window.innerHeight - popupH - 8;
    if (y < 60) y = 60;

    popup.style.left = x + "px";
    popup.style.top = y + "px";

    document.getElementById("bombRadiusInput").value = "";
    clearBombPreview();
    setTimeout(() => document.getElementById("bombRadiusInput").focus(), 40);
}

function hideBombPopup() {
    document.getElementById("bombPopup").classList.add("hidden");
    clearBombPreview();
}

function cancelBomb() {
    hideBombPopup();
}

function confirmBomb() {
    const radius = parseFloat(document.getElementById("bombRadiusInput").value);
    const input = document.getElementById("bombRadiusInput");

    if (!radius || radius <= 0) {
        input.classList.add("input-error");
        setTimeout(() => input.classList.remove("input-error"), 700);
        return;
    }

    const lat = state.bombPendingLat;
    const lng = state.bombPendingLng;

    clearBombPreview();
    hideBombPopup();
    toggleBombMode();

    const { affectedNodes, affectedEdges } = calculateBombEffect(lat, lng, radius);

    const bomb = {
        id: "bomb_" + Date.now(),
        lat,
        lng,
        radius,
        timestamp: new Date().toISOString(),
        affectedNodes: dedupe(affectedNodes),
        affectedEdges: dedupe(affectedEdges),
    };

    const bombs = getBombs();
    bombs.push(bomb);
    saveBombs(bombs);

    syncBlockedToServer(bomb.affectedNodes, bomb.affectedEdges, 1);

    drawBombCircle(bomb);
    triggerExplosionAnimation(lat, lng);

    updateStationBlockedVisuals();
    renderClosureSummary();
    renderBombList();

    const startStationId = document.getElementById("startStation").value;
    if (startStationId) {
        state.reachableEndIds = getReachableDestinations(startStationId);
        populateStationSelects();
    }
    updateSelectionSummary();
    setStatus(`💣 Vụ nổ R=${radius}km — ${affectedNodes.length} ga, ${affectedEdges.length} cạnh bị chặn.`);
}

function onBombRadiusKey(e) {
    if (e.key === "Enter") confirmBomb();
    if (e.key === "Escape") cancelBomb();
}

function previewBombCircle() {
    clearBombPreview();
    const radius = parseFloat(document.getElementById("bombRadiusInput").value);
    if (radius > 0 && state.bombPendingLat !== null) {
        state.bombPreviewCircle = L.circle([state.bombPendingLat, state.bombPendingLng], {
            radius: radius * 1000,
            color: "#ff4500",
            weight: 1.5,
            fillColor: "#ff4500",
            fillOpacity: 0.07,
            dashArray: "6 4",
            interactive: false,
        }).addTo(state.map);
    }
}

function clearBombPreview() {
    if (state.bombPreviewCircle) {
        state.bombPreviewCircle.remove();
        state.bombPreviewCircle = null;
    }
}

function haversineKm(lat1, lng1, lat2, lng2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const sinLat = Math.sin(dLat / 2);
    const sinLng = Math.sin(dLng / 2);
    const a = sinLat * sinLat + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * sinLng * sinLng;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function calculateBombEffect(lat, lng, radiusKm) {
    const affectedNodes = [];
    for (const station of state.stationOptions) {
        const [lon, stLat] = station.geometry;
        if (!Number.isFinite(stLat) || !Number.isFinite(lon)) continue;
        if (haversineKm(lat, lng, stLat, lon) <= radiusKm) {
            for (const stopId of station.stops) affectedNodes.push(stopId);
        }
    }

    const nodeSet = new Set(affectedNodes);
    const affectedEdges = [];
    for (const [edgeId, edge] of state.edgeById) {
        if (nodeSet.has(edge.source_id) || nodeSet.has(edge.dest_id)) {
            affectedEdges.push(edgeId);
            continue;
        }
        // Cũng chặn cạnh đi qua vùng nổ dù hai đầu nút nằm ngoài
        if (Array.isArray(edge.geometry) && edge.geometry.some(([eLon, eLat]) =>
            Number.isFinite(eLat) && Number.isFinite(eLon) &&
            haversineKm(lat, lng, eLat, eLon) <= radiusKm
        )) {
            affectedEdges.push(edgeId);
        }
    }
    return { affectedNodes, affectedEdges };
}

function drawBombCircle(bomb) {
    if (bombCircles.has(bomb.id)) bombCircles.get(bomb.id).remove();

    const circle = L.circle([bomb.lat, bomb.lng], {
        radius: bomb.radius * 1000,
        color: "#ff4500",
        weight: 2,
        fillColor: "#ff4500",
        fillOpacity: 0.06,
        dashArray: "10 5",
    });
    circle.bindTooltip(
        `💣 R=${bomb.radius}km<br>${bomb.affectedNodes.length} ga · ${bomb.affectedEdges.length} cạnh`,
        { sticky: true }
    );
    circle.addTo(state.bombLayer);
    bombCircles.set(bomb.id, circle);
}

function playExplosionSound() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const t = ctx.currentTime;

        // Compressor để âm thanh nghe punchier, không bị vỡ
        const comp = ctx.createDynamicsCompressor();
        comp.threshold.value = -10;
        comp.knee.value = 4;
        comp.ratio.value = 6;
        comp.attack.value = 0.001;
        comp.release.value = 0.15;
        comp.connect(ctx.destination);

        // --- Layer 1: Sub-bass THUD (oscillator quét tần số từ 140 → 18 Hz) ---
        // Tạo cảm giác rung lắc "gut-punch"
        const sub = ctx.createOscillator();
        sub.type = "sine";
        sub.frequency.setValueAtTime(140, t);
        sub.frequency.exponentialRampToValueAtTime(18, t + 0.38);
        const subGain = ctx.createGain();
        subGain.gain.setValueAtTime(7.0, t);
        subGain.gain.exponentialRampToValueAtTime(0.001, t + 0.42);
        sub.connect(subGain);
        subGain.connect(comp);
        sub.start(t);
        sub.stop(t + 0.45);

        // --- Layer 2: Initial CRACK — tiếng nổ sắc ngay lập tức ---
        // Noise burst cực ngắn qua high-pass: nghe như tiếng súng nổ
        const crackLen = Math.floor(ctx.sampleRate * 0.07);
        const crackBuf = ctx.createBuffer(1, crackLen, ctx.sampleRate);
        const crackData = crackBuf.getChannelData(0);
        for (let i = 0; i < crackLen; i++) {
            crackData[i] = (Math.random() * 2 - 1) * Math.exp(-i / (ctx.sampleRate * 0.007));
        }
        const crackSrc = ctx.createBufferSource();
        crackSrc.buffer = crackBuf;
        const crackHp = ctx.createBiquadFilter();
        crackHp.type = "highpass";
        crackHp.frequency.value = 1800;
        const crackGain = ctx.createGain();
        crackGain.gain.setValueAtTime(6.5, t);
        crackSrc.connect(crackHp);
        crackHp.connect(crackGain);
        crackGain.connect(comp);
        crackSrc.start(t);

        // --- Layer 3: Mid-range BOOM — phần thân chính của tiếng nổ ---
        // Bandpass noise quét từ 320 Hz → 60 Hz trong 1 giây
        const boomLen = Math.floor(ctx.sampleRate * 1.0);
        const boomBuf = ctx.createBuffer(1, boomLen, ctx.sampleRate);
        const boomData = boomBuf.getChannelData(0);
        for (let i = 0; i < boomLen; i++) {
            boomData[i] = Math.random() * 2 - 1;
        }
        const boomSrc = ctx.createBufferSource();
        boomSrc.buffer = boomBuf;
        const boomBp = ctx.createBiquadFilter();
        boomBp.type = "bandpass";
        boomBp.frequency.setValueAtTime(320, t);
        boomBp.frequency.exponentialRampToValueAtTime(60, t + 1.0);
        boomBp.Q.value = 0.7;
        const boomGain = ctx.createGain();
        boomGain.gain.setValueAtTime(4.5, t);
        boomGain.gain.exponentialRampToValueAtTime(0.001, t + 1.0);
        boomSrc.connect(boomBp);
        boomBp.connect(boomGain);
        boomGain.connect(comp);
        boomSrc.start(t);

        // --- Layer 4: FIREBALL whoosh — âm thanh lửa cháy phừng ---
        // Bandpass noise ở mid-high (800 Hz), decay chậm — nghe như tiếng lửa
        const fireLen = Math.floor(ctx.sampleRate * 1.4);
        const fireBuf = ctx.createBuffer(1, fireLen, ctx.sampleRate);
        const fireData = fireBuf.getChannelData(0);
        for (let i = 0; i < fireLen; i++) {
            fireData[i] = Math.random() * 2 - 1;
        }
        const fireSrc = ctx.createBufferSource();
        fireSrc.buffer = fireBuf;
        const fireBp = ctx.createBiquadFilter();
        fireBp.type = "bandpass";
        fireBp.frequency.setValueAtTime(900, t + 0.04);
        fireBp.frequency.exponentialRampToValueAtTime(220, t + 1.4);
        fireBp.Q.value = 1.2;
        const fireGain = ctx.createGain();
        fireGain.gain.setValueAtTime(0, t);
        fireGain.gain.linearRampToValueAtTime(2.8, t + 0.06);
        fireGain.gain.exponentialRampToValueAtTime(0.001, t + 1.4);
        fireSrc.connect(fireBp);
        fireBp.connect(fireGain);
        fireGain.connect(comp);
        fireSrc.start(t + 0.04);

        // --- Layer 5: Low RUMBLE đuôi dài — tiếng rung chấn mặt đất ---
        const rumbleLen = Math.floor(ctx.sampleRate * 2.8);
        const rumbleBuf = ctx.createBuffer(1, rumbleLen, ctx.sampleRate);
        const rumbleData = rumbleBuf.getChannelData(0);
        for (let i = 0; i < rumbleLen; i++) {
            rumbleData[i] = Math.random() * 2 - 1;
        }
        const rumbleSrc = ctx.createBufferSource();
        rumbleSrc.buffer = rumbleBuf;
        const rumbleLp = ctx.createBiquadFilter();
        rumbleLp.type = "lowpass";
        rumbleLp.frequency.setValueAtTime(120, t + 0.08);
        rumbleLp.frequency.exponentialRampToValueAtTime(25, t + 2.8);
        const rumbleGain = ctx.createGain();
        rumbleGain.gain.setValueAtTime(3.2, t + 0.08);
        rumbleGain.gain.exponentialRampToValueAtTime(0.001, t + 2.8);
        rumbleSrc.connect(rumbleLp);
        rumbleLp.connect(rumbleGain);
        rumbleGain.connect(comp);
        rumbleSrc.start(t + 0.08);

        setTimeout(() => ctx.close(), 3200);
    } catch (_) {}
}

function triggerExplosionAnimation(lat, lng) {
    playExplosionSound();
    const point = state.map.latLngToContainerPoint([lat, lng]);
    const mapRect = document.getElementById("map").getBoundingClientRect();
    const x = mapRect.left + point.x;
    const y = mapRect.top + point.y;

    const mapEl = document.getElementById("map");
    mapEl.style.animation = "none";
    void mapEl.offsetHeight;
    mapEl.style.animation = "map-shake 0.45s ease-out";
    setTimeout(() => { mapEl.style.animation = ""; }, 480);

    const overlay = document.createElement("div");
    overlay.className = "expl-shockwave-overlay";
    const pctX = ((x / window.innerWidth) * 100).toFixed(1) + "%";
    const pctY = ((y / window.innerHeight) * 100).toFixed(1) + "%";
    overlay.style.setProperty("--cx", pctX);
    overlay.style.setProperty("--cy", pctY);
    document.body.appendChild(overlay);
    setTimeout(() => overlay.remove(), 600);

    const wrapper = document.createElement("div");
    wrapper.className = "bomb-explosion";
    wrapper.style.left = x + "px";
    wrapper.style.top = y + "px";

    wrapper.innerHTML += `<div class="expl-core"></div>`;
    wrapper.innerHTML += `<div class="expl-fireball"></div>`;

    const rings = [
        { d: "0ms",   s: "60px",  c: "#ffffff",  w: "4px",  dur: "0.7s" },
        { d: "60ms",  s: "120px", c: "#ff4500",  w: "3px",  dur: "0.9s" },
        { d: "130ms", s: "200px", c: "#ff8c00",  w: "2.5px",dur: "1.0s" },
        { d: "200ms", s: "310px", c: "#ffd700",  w: "2px",  dur: "1.15s" },
        { d: "280ms", s: "450px", c: "#ff4500",  w: "1.5px",dur: "1.3s" },
        { d: "380ms", s: "620px", c: "#ffffff",  w: "1px",  dur: "1.5s" },
    ];
    for (const r of rings) {
        const el = document.createElement("div");
        el.className = "expl-ring";
        el.style.cssText = `--d:${r.d};--s:${r.s};--c:${r.c};--w:${r.w};--dur:${r.dur}`;
        wrapper.appendChild(el);
    }

    const sparkColors = ["#fff", "#ffe566", "#ffbb00", "#ff7700", "#ff4500", "#ff0000"];
    for (let i = 0; i < 24; i++) {
        const angle = (i / 24) * 360 + (Math.random() * 15 - 7.5);
        const radius = 55 + Math.random() * 90;
        const size = 4 + Math.random() * 5;
        const color = sparkColors[Math.floor(Math.random() * sparkColors.length)];
        const delay = Math.random() * 80;
        const dur = (0.6 + Math.random() * 0.4).toFixed(2) + "s";
        const el = document.createElement("div");
        el.className = "expl-spark";
        el.style.cssText = `--a:${angle.toFixed(1)}deg;--r:${radius.toFixed(0)}px;--sz:${size.toFixed(1)}px;--c:${color};--d:${delay.toFixed(0)}ms;--dur:${dur}`;
        wrapper.appendChild(el);
    }

    const debrisColors = ["#ff4500", "#cc2200", "#ff8800", "#ffcc00"];
    for (let i = 0; i < 12; i++) {
        const angle = (i / 12) * 360 + (Math.random() * 20 - 10);
        const radius = 40 + Math.random() * 70;
        const w = 6 + Math.random() * 8;
        const h = 3 + Math.random() * 4;
        const color = debrisColors[Math.floor(Math.random() * debrisColors.length)];
        const delay = 30 + Math.random() * 100;
        const dur = (0.8 + Math.random() * 0.5).toFixed(2) + "s";
        const el = document.createElement("div");
        el.className = "expl-debris";
        el.style.cssText = `--a:${angle.toFixed(1)}deg;--r:${radius.toFixed(0)}px;--sw:${w.toFixed(0)}px;--sh:${h.toFixed(0)}px;--c:${color};--d:${delay.toFixed(0)}ms;--dur:${dur}`;
        wrapper.appendChild(el);
    }

    const smokeDefs = [
        { ox: "0px",   oy: "0px",   sz: "80px",  d: "350ms", dur: "2.0s", sf: "3.5" },
        { ox: "-20px", oy: "-10px", sz: "60px",  d: "500ms", dur: "2.2s", sf: "2.8" },
        { ox: "18px",  oy: "-8px",  sz: "55px",  d: "450ms", dur: "2.4s", sf: "3.0" },
        { ox: "5px",   oy: "15px",  sz: "70px",  d: "600ms", dur: "2.6s", sf: "3.2" },
    ];
    for (const s of smokeDefs) {
        const el = document.createElement("div");
        el.className = "expl-smoke";
        el.style.cssText = `--ox:${s.ox};--oy:${s.oy};--d:${s.d};--dur:${s.dur};--sf:${s.sf};width:${s.sz};height:${s.sz}`;
        wrapper.appendChild(el);
    }

    document.body.appendChild(wrapper);
    setTimeout(() => wrapper.remove(), 2800);
}

function redrawAllBombs() {
    state.bombLayer.clearLayers();
    bombCircles.clear();
    for (const bomb of getBombs()) drawBombCircle(bomb);
}

function getExclusivelyBlockedByBomb(bombId) {
    const bombs = getBombs();
    const thisBomb = bombs.find(b => b.id === bombId);
    if (!thisBomb) return { nodeIds: [], edgeIds: [], nodes: 0, edges: 0 };

    const remainingBombs = bombs.filter(b => b.id !== bombId);
    const manual = getBlockedConfig();

    const stillBlockedNodes = new Set([
        ...manual.blockedNodes,
        ...remainingBombs.flatMap(b => b.affectedNodes || []),
    ]);
    const stillBlockedEdges = new Set([
        ...manual.blockedEdges,
        ...remainingBombs.flatMap(b => b.affectedEdges || []),
    ]);

    const nodeIds = (thisBomb.affectedNodes || []).filter(n => !stillBlockedNodes.has(n));
    const edgeIds = (thisBomb.affectedEdges || []).filter(e => !stillBlockedEdges.has(e));
    return { nodeIds, edgeIds, nodes: nodeIds.length, edges: edgeIds.length };
}

async function syncBlockedToServer(nodeIds, edgeIds, isBlocked) {
    const requests = [];

    for (const stopId of nodeIds) {
        requests.push(fetchJson(API_ENDPOINTS.findPath.replace("/path/by-stations", "/admin/network/status"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_type: "stop", target_id: stopId, is_blocked: isBlocked }),
        }));
    }

    for (const edgeId of edgeIds) {
        requests.push(fetchJson(API_ENDPOINTS.findPath.replace("/path/by-stations", "/admin/network/status"), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ target_type: "edge", target_id: edgeId, is_blocked: isBlocked }),
        }));
    }

    try {
        await Promise.all(requests);
    } catch (err) {
        console.warn("syncBlockedToServer failed:", err.message);
    }
}

function renderBombList() {
    renderClosureSummary();
}

function removeBomb(bombId) {
    const { nodeIds, edgeIds, nodes: restoredNodes, edges: restoredEdges } = getExclusivelyBlockedByBomb(bombId);

    const newBombs = getBombs().filter(b => b.id !== bombId);
    saveBombs(newBombs);

    if (nodeIds.length > 0 || edgeIds.length > 0) {
        syncBlockedToServer(nodeIds, edgeIds, 0);
    }

    if (bombCircles.has(bombId)) {
        bombCircles.get(bombId).remove();
        bombCircles.delete(bombId);
    }

    updateStationBlockedVisuals();
    renderClosureSummary();
    renderBombList();

    const startStationId = document.getElementById("startStation").value;
    if (startStationId) {
        state.reachableEndIds = getReachableDestinations(startStationId);
        populateStationSelects();
    }
    updateSelectionSummary();

    const msg = (restoredNodes > 0 || restoredEdges > 0)
        ? `Đã gỡ bom. Khôi phục ${restoredNodes} ga, ${restoredEdges} cạnh.`
        : "Đã gỡ bom (các ga vẫn bị chặn bởi vụ nổ khác).";
    setStatus(msg);
}

function clearAllBombs() {
    const effectiveBefore = getEffectiveBlockedConfig();
    const manual = getBlockedConfig();
    const manualNodeSet = new Set(manual.blockedNodes);
    const manualEdgeSet = new Set(manual.blockedEdges);
    const bombOnlyNodeIds = effectiveBefore.blockedNodes.filter(n => !manualNodeSet.has(n));
    const bombOnlyEdgeIds = effectiveBefore.blockedEdges.filter(e => !manualEdgeSet.has(e));
    const bombOnlyNodes = bombOnlyNodeIds.length;

    if (bombOnlyNodeIds.length > 0 || bombOnlyEdgeIds.length > 0) {
        syncBlockedToServer(bombOnlyNodeIds, bombOnlyEdgeIds, 0);
    }

    saveBombs([]);
    state.bombLayer.clearLayers();
    bombCircles.clear();

    updateStationBlockedVisuals();
    renderClosureSummary();
    renderBombList();

    const startStationId = document.getElementById("startStation").value;
    if (startStationId) {
        state.reachableEndIds = getReachableDestinations(startStationId);
        populateStationSelects();
    }
    updateSelectionSummary();

    const msg = bombOnlyNodes > 0
        ? `Đã gỡ tất cả bom. Khôi phục ~${bombOnlyNodes} ga.`
        : "Đã gỡ tất cả bom.";
    setStatus(msg);
}

// ===================== END BOMB SYSTEM =====================

document.addEventListener("DOMContentLoaded", initMapPage);
