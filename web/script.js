const moscowCenter = [55.751244, 37.618423];

const state = {
    map: null,
    stationMarkersVisible: true,
    routeLayer: null,
    stationLayer: null,
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

function initMapPage() {
    if (!document.getElementById("map")) {
        return;
    }

    buildMap();
    bindUiEvents();
    loadAppData();
    renderRouteHistory();
    updateRouteSummary();
    updateStationToggleButton();
}

function buildMap() {
    state.map = L.map("map", { zoomControl: false, preferCanvas: true }).setView(moscowCenter, 11);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; OpenStreetMap &copy; CARTO",
        subdomains: "abcd",
        maxZoom: 19,
    }).addTo(state.map);

    L.control.zoom({ position: "bottomright" }).addTo(state.map);
    state.routeLayer = L.layerGroup().addTo(state.map);
    state.stationLayer = L.layerGroup().addTo(state.map);
}

function bindUiEvents() {
    document.getElementById("stationSearch").addEventListener("input", onSearchInput);
    document.getElementById("togglePanelBtn").addEventListener("click", togglePanel);
    document.getElementById("mobileDrawerHandle").addEventListener("click", togglePanel);
    document.getElementById("startStation").addEventListener("change", onStartStationChange);
    document.getElementById("endStation").addEventListener("change", updateSelectionSummary);
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
            radius: 5,
            color,
            weight: 1.5,
            fillColor: color,
            fillOpacity: 0.92,
        });

        marker.on("click", () => openStationPanel(station));
        marker.bindTooltip(station.name, { direction: "top", opacity: 0.9 });
        marker.addTo(state.stationLayer);
        station.marker = marker;
    }

    updateVisibleStationCount();
}

function updateStationBlockedVisuals() {
    const blockedNodes = new Set(getBlockedConfig().blockedNodes);

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

function isStationFullyBlocked(station, blockedNodes = new Set(getBlockedConfig().blockedNodes)) {
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
        button.innerHTML = `
            <strong>${station.name}</strong>
            <span>${station.nameEn || station.lineId}</span>
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
    const blockedConfig = getBlockedConfig();
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
        const result = await findBestPath(startCandidates, endCandidates, blockedConfig);
        renderPath(result, algorithm);
    } catch (error) {
        clearRouteLayer();
        setStatus(`Không tìm được: ${error.message}`, true);
    } finally {
        findButton.disabled = false;
        findButton.innerText = "Tìm đường";
    }
}

async function findBestPath(startCandidates, endCandidates, blockedConfig) {
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
        }).addTo(state.routeLayer);

        const endMarker = L.circleMarker(latLngs[latLngs.length - 1], {
            radius: 8,
            color: "#6ee7b7",
            weight: 2,
            fillColor: "#6ee7b7",
            fillOpacity: 1,
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
    const stationNames = [];
    let previous = null;

    for (const nodeId of pathNodes) {
        const station = state.stationByRouteStop.get(nodeId);
        const name = station?.name || state.routeStopNameById.get(nodeId) || null;
        if (!name || name === previous) {
            continue;
        }
        stationNames.push(name);
        previous = name;
    }

    return stationNames;
}

function renderRouteStations(stationNames) {
    const container = document.getElementById("routeStationsList");
    container.innerHTML = "";

    if (stationNames.length === 0) {
        container.innerHTML = '<div class="empty-state">Không có dữ liệu.</div>';
        return;
    }

    for (const [index, name] of stationNames.entries()) {
        const item = document.createElement("div");
        item.className = "route-station-item";
        item.innerHTML = `<span>${String(index + 1).padStart(2, "0")}</span><strong>${name}</strong>`;
        container.appendChild(item);
    }
}

function renderClosureSummary() {
    const container = document.getElementById("closureSummary");
    const blockedConfig = getBlockedConfig();

    const blockedStationNames = blockedConfig.blockedNodes
        .map((stopId) => state.stationByRouteStop.get(stopId)?.name || state.routeStopNameById.get(stopId) || stopId)
        .slice(0, 4);

    const blockedEdgeNames = blockedConfig.blockedEdges.slice(0, 4);

    container.innerHTML = `
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

function formatCost(value) {
    if (value === undefined || value === null || Number.isNaN(Number(value))) {
        return "--";
    }
    return `${Number(value).toFixed(2)}`;
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

    const blockedConfig = getBlockedConfig();
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

document.addEventListener("DOMContentLoaded", initMapPage);
