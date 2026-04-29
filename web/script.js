// Moscow Metro Pathfinder - Frontend
// Uses same-origin proxy endpoints in web/app.py

let map;
let stationMarkers = [];
let edgeLines = [];
let pathLines = [];
let stationData = {};
let stationList = [];
let edgesData = [];
let edgeIndex = {};
let pathVisible = true;
let stationsVisible = true;
let edgesVisible = true;
let controlsVisible = true;

// Initialize the map
async function initMap() {
    map = L.map('map').setView([55.7558, 37.6173], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    await loadData();
    
    // Add event listeners for search input - autocomplete dropdown
    const stationSearchInput = document.getElementById('stationSearch');
    if (stationSearchInput) {
        stationSearchInput.addEventListener('input', (event) => {
            updateSearchList(event.target.value);
        });
        stationSearchInput.addEventListener('focus', (event) => {
            if (event.target.value.trim()) {
                updateSearchList(event.target.value);
            }
        });
        stationSearchInput.addEventListener('blur', () => {
            setTimeout(() => {
                document.getElementById('stationSearchList').style.display = 'none';
            }, 200);
        });
    }
}

// // Load data from root API and edge list
async function loadData() {
    clearAll();
    
    try {
        // Load station list from station_dict.json
        const stationListResponse = await fetch('/api/station_list');
        if (!stationListResponse.ok) {
            const errorBody = await stationListResponse.text();
            throw new Error(`Station list fetch failed: ${stationListResponse.status} - ${errorBody}`);
        }
        stationList = await stationListResponse.json();

        // Load edges from edge_list.json
        const edgesResponse = await fetch('/api/edge_list');
        if (!edgesResponse.ok) {
            const errorBody = await edgesResponse.text();
            throw new Error(`Edges fetch failed: ${edgesResponse.status} - ${errorBody}`);
        }
        edgesData = await edgesResponse.json();

        stationData = {};
        edgeIndex = {};

        // Build station lookup map from station_dict
        stationList.forEach(station => {
            stationData[station.id] = {
                id: station.id,
                name: station.name,
                name_en: station.name_en,
                lat: station.geometry ? station.geometry[1] : 0,
                lon: station.geometry ? station.geometry[0] : 0,
                line_id: station.line_id,
                colour: station.colour,
                stops: station.stops || [] // Array of stop IDs for pathfinding
            };
        });

        // Index edges for route highlighting
        edgesData.forEach(edge => {
            if (edge.edge_id) {
                edgeIndex[edge.edge_id] = edge;
            }
        });

        // Populate dropdown selects
        populateStationDropdowns();

        // Render stations and edges - use stationData which has processed lat/lon
        const validStations = Object.values(stationData).filter(s => s.lat && s.lon);
        renderStations(validStations);
        renderEdges(edgesData);
        updateStats(validStations.length);
    } catch (error) {
        console.error("Error loading data:", error);
        document.getElementById('routeMessage').textContent = '❌ ' + error.message;
    }
}

// Populate station dropdowns
function populateStationDropdowns() {
    const startSelect = document.getElementById('startStation');
    const endSelect = document.getElementById('endStation');
    
    // Clear existing options except first one
    startSelect.innerHTML = '<option value="">-- Select start station --</option>';
    endSelect.innerHTML = '<option value="">-- Select end station --</option>';
    
    // Sort stations by name for easier selection
    const sortedStations = [...stationList].sort((a, b) => a.name.localeCompare(b.name));
    
    sortedStations.forEach(station => {
        const optionStart = document.createElement('option');
        optionStart.value = station.id;
        optionStart.textContent = `${station.name} (Line ${station.line_id})`;
        startSelect.appendChild(optionStart);
        
        const optionEnd = document.createElement('option');
        optionEnd.value = station.id;
        optionEnd.textContent = `${station.name} (Line ${station.line_id})`;
        endSelect.appendChild(optionEnd);
    });
}

// Find shortest path between two stations
async function findPath() {
    const startId = document.getElementById('startStation').value;
    const endId = document.getElementById('endStation').value;
    const routeMessage = document.getElementById('routeMessage');
    routeMessage.textContent = '';
    clearPath();

    if (!startId || !endId) {
        routeMessage.textContent = '⚠️ Select both start and end stations.';
        return;
    }

    if (startId === endId) {
        routeMessage.textContent = '⚠️ Start and end stations must be different.';
        return;
    }

    const startStation = stationData[startId];
    const endStation = stationData[endId];
    
    if (!startStation || !endStation) {
        routeMessage.textContent = '❌ Invalid station selected.';
        return;
    }

    if (!startStation.stops || startStation.stops.length === 0) {
        routeMessage.textContent = '❌ Start station has no stops.';
        return;
    }

    if (!endStation.stops || endStation.stops.length === 0) {
        routeMessage.textContent = '❌ End station has no stops.';
        return;
    }

    try {
        // Map station_id to stop_id (use first stop)
        const startStopId = startStation.stops[0];
        const endStopId = endStation.stops[0];
        
        // Remove previous special markers
        removeSpecialMarker(startMarker);
        removeSpecialMarker(endMarker);
        
        // Add special markers for start and end stations
        startMarker = createSpecialMarker(startStation.lat, startStation.lon, 'start', startStation);
        endMarker = createSpecialMarker(endStation.lat, endStation.lon, 'end', endStation);

        const requestBody = JSON.stringify({
            start_id: startStopId,
            target_id: endStopId,
            blocked_edges: [],
            blocked_nodes: []
        });

        const response = await fetch('/api/find-path', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: requestBody
        });

        if (!response.ok) {
            const errorBody = await response.text();
            let errorMsg = errorBody;
            try {
                const errorJson = JSON.parse(errorBody);
                errorMsg = errorJson.detail || errorJson.error || errorBody;
            } catch (e) {}
            throw new Error(`HTTP ${response.status}: ${errorMsg}`);
        }

        const result = await response.json();
        if (result.status !== 'success' || !result.result) {
            throw new Error(result.detail || result.error || 'Root API returned no route.');
        }

        const pathEdges = result.result.path_edges || [];
        const pathNodes = result.result.path_nodes || [];

        if (!pathEdges.length) {
            routeMessage.textContent = '⚠️ No path found for the selected stations.';
            return;
        }

        highlightPath(pathEdges, pathNodes);
        routeMessage.textContent = `✓ ${startStation.name} → ${endStation.name} | ${pathNodes.length} stops | ${result.result.total_distance_meters} m`;
    } catch (error) {
        console.error('Path error:', error);
        routeMessage.textContent = '❌ ' + error.message;
    }
}

function highlightPath(edgeIds, nodeIds) {
    clearPath();
    const pathCoords = [];
    edgeIds.forEach(edgeId => {
        const edge = edgeIndex[edgeId];
        if (!edge || !edge.geometry) return;
        const coords = edge.geometry.map(g => [g[1], g[0]]);
        const line = L.polyline(coords, {
            color: '#00FF00',
            weight: 6,
            opacity: 0.9
        }).addTo(map);
        pathLines.push(line);
        pathCoords.push(...coords);
    });

    if (pathCoords.length) {
        const bounds = L.latLngBounds(pathCoords);
        map.fitBounds(bounds, {padding: [30, 30]});
    }
}

function clearPath() {
    pathLines.forEach(line => map.removeLayer(line));
    pathLines = [];
}

// Render station markers
function renderStations(stations) {
    stations.forEach(station => {
        const marker = L.circleMarker([station.lat, station.lon], {
            radius: 8,
            fillColor: station.colour || '#0072BA',
            color: '#fff',
            weight: 2,
            fillOpacity: 0.9
        });

        marker.bindPopup(`
            <div style="min-width: 150px;">
                <b style="color: ${station.colour || '#0072BA'};">${station.name}</b><br>
                <small style="color: #666;">Line ${station.line_id || 'N/A'}</small>
            </div>
        `);

        marker.on('click', () => showStationInfo(station));
        marker.addTo(map);
        stationMarkers.push(marker);
    });
}

let startMarker = null;
let endMarker = null;
let searchedMarker = null;

function createSpecialMarker(lat, lon, type, station) {
    let marker;
    if (type === 'start') {
        marker = L.circleMarker([lat, lon], {
            radius: 12,
            fillColor: '#00FF00',
            color: '#fff',
            weight: 3,
            fillOpacity: 1
        });
    } else if (type === 'end') {
        marker = L.circleMarker([lat, lon], {
            radius: 12,
            fillColor: '#FF0000',
            color: '#fff',
            weight: 3,
            fillOpacity: 1
        });
    } else if (type === 'searched') {
        marker = L.circleMarker([lat, lon], {
            radius: 11,
            fillColor: '#FFD700',
            color: '#fff',
            weight: 3,
            fillOpacity: 1
        });
    }
    
    if (marker) {
        marker.bindPopup(`<b>${station.name}</b><br>Line ${station.line_id || 'N/A'}`);
        marker.addTo(map);
    }
    return marker;
}

function removeSpecialMarker(markerRef) {
    if (markerRef) {
        map.removeLayer(markerRef);
    }
}

// Render edges/lines
function renderEdges(edges) {
    edges.forEach(edge => {
        if (edge.geometry && edge.geometry.length >= 2) {
            const coords = edge.geometry.map(g => [g[1], g[0]]); // Convert [lon, lat] to [lat, lon]
            
            let color = edge.colour || '#0072BA';
            let weight = 3;
            let opacity = 0.8;
            let dashArray = null;

            // Transfer edges - dashed
            if (edge.edge_type === 'transfer') {
                color = '#FF4500';
                dashArray = '8, 8';
                weight = 3;
            }

            const line = L.polyline(coords, {
                color: color,
                weight: weight,
                opacity: opacity,
                dashArray: dashArray
            }).addTo(map);
            edgeLines.push(line);
        }
    });
}

// Show station information
function showStationInfo(station) {
    document.getElementById('stationName').textContent = station.name;
    document.getElementById('stationNameRu').textContent = station.name;
    document.getElementById('stationType').textContent = `Line ${station.line_id || 'N/A'} | ${station.colour || 'N/A'}`;
    document.getElementById('stationCoords').textContent = 
        `${station.lat.toFixed(6)}, ${station.lon.toFixed(6)}`;
    document.getElementById('stationInfo').style.display = 'block';
}

// Close station info panel
function closeStationPanel() {
    document.getElementById('stationInfo').style.display = 'none';
}

// Update statistics
function updateStats(stationCount) {
    document.getElementById('stats').innerHTML = `
        <p>🚇 <strong>${stationCount}</strong> stations loaded</p>
    `;
}

// Center map to Moscow
function centerMap() {
    map.setView([55.7558, 37.6173], 12);
}

// Toggle stations visibility
function toggleStations() {
    stationsVisible = !stationsVisible;
    stationMarkers.forEach(marker => {
        if (stationsVisible) {
            marker.addTo(map);
        } else {
            map.removeLayer(marker);
        }
    });
}

// Toggle edges/lines visibility
function toggleEdges() {
    edgesVisible = !edgesVisible;
    edgeLines.forEach(line => {
        if (edgesVisible) {
            line.addTo(map);
        } else {
            map.removeLayer(line);
        }
    });
}

// Toggle path visibility
function togglePathVisibility() {
    pathVisible = !pathVisible;
    pathLines.forEach(line => {
        if (pathVisible) {
            line.addTo(map);
        } else {
            map.removeLayer(line);
        }
    });
}

// Clear all markers and lines
function clearAll() {
    stationMarkers.forEach(marker => map.removeLayer(marker));
    edgeLines.forEach(line => map.removeLayer(line));
    clearPath();
    removeSpecialMarker(startMarker);
    removeSpecialMarker(endMarker);
    removeSpecialMarker(searchedMarker);
    startMarker = null;
    endMarker = null;
    searchedMarker = null;
    stationMarkers = [];
    edgeLines = [];
    closeStationPanel();
    document.getElementById('routeMessage').textContent = '';
    document.getElementById('stationSearch').value = '';
    document.getElementById('stationSearchList').style.display = 'none';
}

// Update search list based on input
function updateSearchList(query) {
    const searchList = document.getElementById('stationSearchList');
    searchList.innerHTML = '';
    
    if (!query.trim()) {
        searchList.style.display = 'none';
        return;
    }
    
    const normalized = query.toLowerCase();
    const matches = [];
    
    // Find exact matches first
    for (const id in stationData) {
        const station = stationData[id];
        if (station && station.name && station.name.toLowerCase() === normalized) {
            matches.unshift({ id, station, isExact: true });
        }
    }
    
    // Then partial matches
    for (const id in stationData) {
        const station = stationData[id];
        if (station && station.name && station.name.toLowerCase().includes(normalized) && 
            station.name.toLowerCase() !== normalized) {
            matches.push({ id, station, isExact: false });
        }
    }
    
    if (matches.length === 0) {
        searchList.style.display = 'none';
        return;
    }
    
    matches.slice(0, 10).forEach(({ id, station }) => {
        const item = document.createElement('div');
        item.className = 'search-item';
        item.textContent = `${station.name} (Line ${station.line_id || 'N/A'})`;
        item.onclick = () => selectStationFromSearch(id, station);
        searchList.appendChild(item);
    });
    
    searchList.style.display = 'block';
}

// Select station from search dropdown
function selectStationFromSearch(stationId, station) {
    document.getElementById('stationSearch').value = station.name;
    document.getElementById('stationSearchList').style.display = 'none';
    
    // Remove previous searched marker
    removeSpecialMarker(searchedMarker);
    
    // Add new special marker for searched station
    if (station.lat && station.lon) {
        searchedMarker = createSpecialMarker(station.lat, station.lon, 'searched', station);
    }
    
    // Focus map on station
    if (station.lat && station.lon) {
        map.setView([station.lat, station.lon], 16);
    }
    showStationInfo(station);
}

// Search and focus on single station
function searchStation() {
    const query = document.getElementById('stationSearch').value.trim();
    if (!query) {
        return;
    }
    
    const stationId = findStationByName(query);
    if (!stationId) {
        alert('Station not found. Try another name.');
        return;
    }
    
    const station = stationData[stationId];
    if (station && station.lat && station.lon) {
        map.setView([station.lat, station.lon], 16);
        showStationInfo(station);
        document.getElementById('stationSearch').value = '';
    }
}

function findStationByName(name) {
    const normalized = name.toLowerCase();
    for (const id in stationData) {
        const station = stationData[id];
        if (station && station.name) {
            if (station.name.toLowerCase() === normalized) {
                return id;
            }
        }
    }
    // Return first partial match
    for (const id in stationData) {
        const station = stationData[id];
        if (station && station.name && station.name.toLowerCase().includes(normalized)) {
            return id;
        }
    }
    return null;
}

// Toggle controls panel visibility
function toggleControls() {
    controlsVisible = !controlsVisible;
    const controlsPanel = document.getElementById('controls');
    if (controlsVisible) {
        controlsPanel.style.display = 'block';
    } else {
        controlsPanel.style.display = 'none';
    }
}

// Initialize on page load
initMap();