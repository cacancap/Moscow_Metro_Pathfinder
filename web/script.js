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
}

function bindUiEvents() {
    document.getElementById("stationSearch").addEventListener("input", onSearchInput);
    document.getElementById("togglePanelBtn").addEventListener("click", togglePanel);
    document.getElementById("mobileDrawerHandle").addEventListener("click", togglePanel);
    document.getElementById("startStation").addEventListener("change", onStartStationChange);
}

async function loadAppData() {
    setStatus("Đang tải dữ liệu ga và cạnh từ API...");

    try {
        const [stationCatalog, routeStops, edgeList] = await Promise.all([
            fetchJson(API_ENDPOINTS.stationCatalog),
            fetchJson(API_ENDPOINTS.routeStations),
            fetchJson(API_ENDPOINTS.edgeList),
        ]);

        state.stationCatalog = stationCatalog;
        state.routeStops = routeStops;
        state.routeStopIds = new Set(routeStops.map((station) => station.id));
        state.routeStopNameById = new Map(routeStops.map((station) => [station.id, station.name]));
        state.edgeById = new Map(edgeList.map((edge) => [edge.edge_id, edge]));
        state.adjacency = buildAdjacency(edgeList);

        buildStationOptionIndex();
        populateStationSelects();
        renderStationMarkers();
        renderClosureSummary();
        setStatus("Dữ liệu đã sẵn sàng. Chọn ga hoặc click vào marker để bắt đầu.");
    } catch (error) {
        setStatus(`Không tải được dữ liệu: ${error.message}`, true);
    }
}

function buildStationOptionIndex() {
    const stationOptions = [];

    for (const station of state.stationCatalog) {
        const validStops = Array.isArray(station.stops)
            ? station.stops.filter((stopId) => state.routeStopIds.has(stopId))
            : [];

        const routeStopId = validStops[0] || null;
        if (!routeStopId) {
            continue;
        }

        const option = {
            stationId: station.id,
            routeStopId,
            name: station.name || "Unknown",
            nameEn: station.name_en || "",
            colour: station.colour || "gray",
            lineId: Array.isArray(station.line_id) ? station.line_id.join(", ") : (station.line_id || "?"),
            geometry: station.geometry || [],
            stops: validStops,
        };

        stationOptions.push(option);
        state.stationById.set(option.stationId, option);
        state.stationByRouteStop.set(option.routeStopId, option);
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

    const placeholderStart = new Option("Chọn ga đi", "");
    const placeholderEnd = new Option("Chọn ga đến", "");
    startSelect.add(placeholderStart);
    endSelect.add(placeholderEnd);

    for (const station of state.stationOptions) {
        const label = `[${station.lineId}] ${station.name}${station.nameEn ? ` / ${station.nameEn}` : ""}`;
        startSelect.add(new Option(label, station.routeStopId));
        if (!state.reachableEndIds || state.reachableEndIds.has(station.routeStopId)) {
            endSelect.add(new Option(label, station.routeStopId));
        }
    }

    startSelect.value = currentStart && state.stationOptions.some((station) => station.routeStopId === currentStart) ? currentStart : "";
    endSelect.value = currentEnd && [...endSelect.options].some((option) => option.value === currentEnd) ? currentEnd : "";
}

function renderStationMarkers() {
    state.stationLayer.clearLayers();

    for (const station of state.stationOptions) {
        const [lon, lat] = station.geometry;
        if (!Number.isFinite(lon) || !Number.isFinite(lat)) {
            continue;
        }

        const marker = L.circleMarker([lat, lon], {
            radius: 5,
            color: resolveLineColor(station.colour),
            weight: 1.5,
            fillColor: resolveLineColor(station.colour),
            fillOpacity: 0.9,
        });

        marker.on("click", () => openStationPanel(station));
        marker.bindTooltip(station.name, { direction: "top", opacity: 0.9 });
        marker.addTo(state.stationLayer);
        station.marker = marker;
    }
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
    panel.classList.remove("hidden");

    document.getElementById("stationName").innerText = station.name;
    document.getElementById("stationNameEn").innerText = station.nameEn || "-";
    document.getElementById("stationLine").innerText = station.lineId || "-";
    document.getElementById("stationStops").innerText = station.stops.join(", ");
    document.getElementById("stationCoords").innerText = `${station.geometry[1].toFixed(5)}, ${station.geometry[0].toFixed(5)}`;

    document.getElementById("useAsStartBtn").onclick = () => {
        setStartStation(station.routeStopId);
    };
    document.getElementById("useAsEndBtn").onclick = () => {
        document.getElementById("endStation").value = station.routeStopId;
    };
}

function closeStationPanel() {
    document.getElementById("stationInfo").classList.add("hidden");
}

async function findPath() {
    const startId = document.getElementById("startStation").value;
    const endId = document.getElementById("endStation").value;
    const algorithm = document.getElementById("algorithm").value;
    const blockedConfig = getBlockedConfig();

    if (!startId || !endId) {
        setStatus("Chọn đủ ga đi và ga đến trước khi chạy.", true);
        return;
    }

    if (startId === endId) {
        setStatus("Ga đi và ga đến đang trùng nhau.", true);
        return;
    }

    setStatus("Đang tính lộ trình từ API...");
    setMetricValues("--", "--", "--");

    try {
        const payload = await fetchJson(API_ENDPOINTS.findPath, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                start_id: startId,
                target_id: endId,
                blocked_edges: blockedConfig.blockedEdges,
                blocked_nodes: blockedConfig.blockedNodes,
            }),
        });

        renderPath(payload.result, algorithm);
    } catch (error) {
        clearRouteLayer();
        setStatus(`Không tìm được lộ trình: ${error.message}`, true);
    }
}

function renderPath(result, algorithm) {
    clearRouteLayer();

    const latLngs = [];
    for (const edgeId of result.path_edges || []) {
        const edge = state.edgeById.get(edgeId);
        if (!edge) {
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
            color: "#ff6b4a",
            weight: 6,
            opacity: 0.9,
            lineJoin: "round",
        }).addTo(state.routeLayer);

        const startMarker = L.circleMarker(latLngs[0], {
            radius: 8,
            color: "#ffe082",
            weight: 2,
            fillColor: "#ffe082",
            fillOpacity: 1,
        }).addTo(state.routeLayer);

        const endMarker = L.circleMarker(latLngs[latLngs.length - 1], {
            radius: 8,
            color: "#74f0b2",
            weight: 2,
            fillColor: "#74f0b2",
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

    setMetricValues(formatCost(result.total_distance_meters), String(result.node_count || 0), `${algorithm.toUpperCase()}`);
    setStatus(`
        <strong>${startStation?.name || "Unknown"}</strong> đến <strong>${endStation?.name || "Unknown"}</strong><br>
        Cost từ API: <strong>${formatCost(result.total_distance_meters)}</strong><br>
        Số node duyệt trên route: <strong>${result.node_count}</strong><br>
        Blocked stations: <strong>${blockedConfig.blockedNodes.length}</strong>,
        blocked edges: <strong>${blockedConfig.blockedEdges.length}</strong>
    `);

    renderRouteStations(stationNames);
    saveRouteHistory({
        start: startStation?.name || result.origin,
        end: endStation?.name || result.destination,
        algorithm,
        cost: result.total_distance_meters,
        nodeCount: result.node_count,
        timestamp: new Date().toISOString(),
    });
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
        container.innerText = "Không có ga để hiển thị.";
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

function toggleStations() {
    state.stationMarkersVisible = !state.stationMarkersVisible;
    if (state.stationMarkersVisible) {
        state.stationLayer.addTo(state.map);
    } else {
        state.stationLayer.remove();
    }
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
    setStatus("Đã xóa route hiện tại.");
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
    const startId = document.getElementById("startStation").value;
    state.reachableEndIds = startId ? getReachableDestinations(startId) : null;
    populateStationSelects();

    const endSelect = document.getElementById("endStation");
    if (startId && !endSelect.value) {
        setStatus(`Đã lọc ${Math.max((state.reachableEndIds?.size || 1) - 1, 0)} ga đích có thể đi đến từ ga xuất phát hiện tại.`);
    }
}

function setStartStation(routeStopId) {
    document.getElementById("startStation").value = routeStopId;
    onStartStationChange();
}

function getReachableDestinations(startId) {
    const blockedConfig = getBlockedConfig();
    const blockedNodes = new Set(blockedConfig.blockedNodes);
    const blockedEdges = new Set(blockedConfig.blockedEdges);
    const visited = new Set();
    const queue = [startId];

    if (blockedNodes.has(startId)) {
        return new Set();
    }

    visited.add(startId);

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
        if (visited.has(station.routeStopId) && station.routeStopId !== startId) {
            reachableStations.add(station.routeStopId);
        }
    }

    return reachableStations;
}

document.addEventListener("DOMContentLoaded", initMapPage);
