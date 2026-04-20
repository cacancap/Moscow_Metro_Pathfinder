// Moscow Metro Pathfinder
// Using: 03_connected_network (nodes_with_hubs + edges_with_hubs) + 04_final_output (station_metadata)

let map;
let stationMarkers = [];
let edgeLines = [];
let stationData = {};

// Initialize the map
async function initMap() {
    map = L.map('map').setView([55.7558, 37.6173], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    await loadData();
}

// Load data from 03_connected_network + 04_final_output
async function loadData() {
    clearMap();
    
    try {
        const [nodesResponse, edgesResponse, metaResponse] = await Promise.all([
            fetch('/data/processed/Khanh/03_connected_network/nodes_with_hubs.json'),
            fetch('/data/processed/Khanh/03_connected_network/edges_with_hubs.json'),
            fetch('/data/processed/Khanh/04_final_output/station_metadata.json')
        ]);

        const nodes = await nodesResponse.json();
        const edges = await edgesResponse.json();
        const metadata = await metaResponse.json();

        stationData = {};
        const stations = [];
        const hubs = [];

        // Process nodes - combine with metadata for names
        nodes.forEach(node => {
            const meta = metadata[node.id] || {};
            stationData[node.id] = {
                id: node.id,
                name_en: node.name_en || meta.name_en || meta.name_ru || node.id,
                name_ru: node.name_ru || meta.name_ru || node.id,
                type: node.type,
                coords: node.coords,
                lat: node.coords[1],
                lon: node.coords[0],
                colour: node.colour,
                is_hub: node.is_hub
            };

            if (node.type === 'station') {
                stations.push(stationData[node.id]);
            } else if (node.type === 'hub') {
                hubs.push(stationData[node.id]);
            }
        });

        renderStations(stations, hubs);
        renderEdges(edges, stationData);
        updateStats(stations.length, hubs.length);
    } catch (error) {
        console.error("Error loading data:", error);
    }
}

// Render station markers with bright colors
function renderStations(stations, hubs) {
    // Render regular stations - bright colors based on line
    stations.forEach(station => {
        const marker = L.circleMarker([station.lat, station.lon], {
            radius: 7,
            fillColor: station.colour || '#00BFFF',
            color: '#fff',
            weight: 2,
            fillOpacity: 1
        });

        marker.bindPopup(`
            <div style="min-width: 150px;">
                <b style="color: ${station.colour || '#00BFFF'};">${station.name_en}</b><br>
                <span style="color: #666;">${station.name_ru}</span><br>
                <small style="color: #999;">Station</small>
            </div>
        `);

        marker.on('click', () => showStationInfo(station));
        marker.addTo(map);
        stationMarkers.push(marker);
    });

    // Render hubs - bright orange-red
    hubs.forEach(hub => {
        const marker = L.circleMarker([hub.lat, hub.lon], {
            radius: 12,
            fillColor: '#FF4500',
            color: '#fff',
            weight: 3,
            fillOpacity: 1
        });

        marker.bindPopup(`
            <div style="min-width: 180px;">
                <b style="color: #FF4500;">🚇 Transfer Hub</b><br>
                <span style="color: #666;">${hub.name_ru}</span><br>
                <small style="color: #999;">Multiple lines</small>
            </div>
        `);

        marker.on('click', () => showStationInfo(hub));
        marker.addTo(map);
        stationMarkers.push(marker);
    });
}

// Render edges/lines from edges_with_hubs.json
function renderEdges(edges, stations) {
    edges.forEach(edge => {
        const start = stations[edge.source];
        const end = stations[edge.target];

        if (start && end && start.lat && end.lat) {
            let color = '#00BFFF';
            let weight = 3;
            let opacity = 0.8;
            let dashArray = null;

            // Use edge colour if available
            if (edge.colour) {
                color = edge.colour;
            } else if (start.colour) {
                // Fallback to station colour
                color = start.colour;
            }

            // Transfer edges - dashed
            if (edge.type === 'transfer') {
                color = '#FF4500';
                dashArray = '8, 8';
                weight = 4;
            }

            // Skip platform edges (very short, not visible)
            if (edge.type === 'platform') {
                return;
            }

            const line = L.polyline([[start.lat, start.lon], [end.lat, end.lon]], {
                color: color,
                weight: weight,
                opacity: opacity,
                dashArray: dashArray
            }).addTo(map);
            edgeLines.push(line);
        }
    });
}

// Show station information panel
function showStationInfo(station) {
    document.getElementById('stationName').textContent = station.name_en || station.name_ru;
    document.getElementById('stationNameRu').textContent = station.name_ru || 'N/A';
    document.getElementById('stationType').textContent = station.type + (station.colour ? ` (${station.colour})` : '');
    document.getElementById('stationCoords').textContent = 
        `${station.lat.toFixed(6)}, ${station.lon.toFixed(6)}`;
    document.getElementById('stationInfo').style.display = 'block';
}

// Close station info panel
function closeStationPanel() {
    document.getElementById('stationInfo').style.display = 'none';
}

// Search station by name
function searchStation() {
    const query = document.getElementById('stationSearch').value.toLowerCase();
    const resultsDiv = document.getElementById('searchResults');
    
    if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
    }

    const matches = Object.values(stationData)
        .filter(station => 
            (station.name_en && station.name_en.toLowerCase().includes(query)) || 
            (station.name_ru && station.name_ru.toLowerCase().includes(query))
        )
        .slice(0, 10);

    if (matches.length > 0) {
        resultsDiv.innerHTML = matches.map(station => `
            <div class="search-item" onclick="focusStation('${station.id}')">
                <strong>${station.name_en || station.name_ru}</strong><br>
                <small>${station.name_ru}</small>
            </div>
        `).join('');
        resultsDiv.style.display = 'block';
    } else {
        resultsDiv.style.display = 'none';
    }
}

// Focus on a specific station
function focusStation(stationId) {
    const station = stationData[stationId];
    if (station) {
        map.setView([station.lat, station.lon], 15);
        showStationInfo(station);
        document.getElementById('searchResults').style.display = 'none';
    }
}

// Update statistics display
function updateStats(stationCount, hubCount) {
    document.getElementById('stats').innerHTML = `
        <p>🚇 Stations: <strong>${stationCount}</strong></p>
        <p>🔄 Transfer Hubs: <strong>${hubCount}</strong></p>
    `;
}

// Center map to Moscow
function centerMap() {
    map.setView([55.7558, 37.6173], 12);
}

// Toggle stations visibility
function toggleStations() {
    stationMarkers.forEach(marker => {
        if (map.hasLayer(marker)) {
            map.removeLayer(marker);
        } else {
            marker.addTo(map);
        }
    });
}

// Clear all markers and lines
function clearMap() {
    stationMarkers.forEach(marker => map.removeLayer(marker));
    edgeLines.forEach(line => map.removeLayer(line));
    stationMarkers = [];
    edgeLines = [];
    closeStationPanel();
}

// Initialize on page load
initMap();