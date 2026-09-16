/**
 * RAAH-AI Northeast Disaster Resilient Emergency Routing Engine
 * Frontend Map Client & Real-Time Dashboard Controller
 */

// Global State
let map = null;
let currentTileLayer = null;
let activeRouteLayer = null;
let blockedRouteLayer = null;
let hazardCircles = [];
let hospitalMarkers = [];
let originMarker = null;
let destMarker = null;
let websocketClient = null;

// Corridor Nodes & Hospitals Master Directory
const corridorDirectory = {
    nodes: {
        "paltan_bazar": { name: "Guwahati Paltan Bazar / Station", lat: 26.1804, lng: 91.7539, elevation_m: 55, city: "Guwahati" },
        "gmch": { name: "GMCH Trauma Center (Bhangagarh)", lat: 26.1558, lng: 91.7772, elevation_m: 62, city: "Guwahati" },
        "dispur": { name: "Dispur Capital Complex", lat: 26.1433, lng: 91.7898, elevation_m: 58, city: "Guwahati" },
        "downtown": { name: "Down Town Hospital (Dispur)", lat: 26.1360, lng: 91.7925, elevation_m: 60, city: "Guwahati" },
        "gau_airport": { name: "Guwahati Airport (GAU)", lat: 26.1061, lng: 91.5859, elevation_m: 49, city: "Guwahati" },
        "excelcare": { name: "Excelcare National Hospital", lat: 26.1265, lng: 91.6872, elevation_m: 52, city: "Guwahati" },
        "khanapara": { name: "Khanapara Gateway Point", lat: 26.1154, lng: 91.8217, elevation_m: 72, city: "Guwahati" },
        "jorabat": { name: "Jorabat Highway Junction", lat: 26.0963, lng: 91.8767, elevation_m: 115, city: "Border" },
        "byrnihat": { name: "Byrnihat (Umtrew River Point)", lat: 26.0489, lng: 91.8845, elevation_m: 185, city: "Ri-Bhoi" },
        "nongpoh": { name: "Nongpoh Town (Ri-Bhoi HQ)", lat: 25.9034, lng: 91.8803, elevation_m: 540, city: "Ri-Bhoi" },
        "nongpoh_civil": { name: "Nongpoh Civil Hospital", lat: 25.9015, lng: 91.8790, elevation_m: 545, city: "Ri-Bhoi" },
        "umsning": { name: "Umsning Junction (NH6)", lat: 25.7533, lng: 91.9056, elevation_m: 880, city: "Ri-Bhoi" },
        "barapani_umiam": { name: "Barapani (Umiam Lake Bridge)", lat: 25.6601, lng: 91.9167, elevation_m: 1040, city: "East Khasi Hills" },
        "mawlai": { name: "Mawlai Checkpoint", lat: 25.6022, lng: 91.8895, elevation_m: 1420, city: "Shillong" },
        "shillong_center": { name: "Shillong Police Bazar / Central Hub", lat: 25.5788, lng: 91.8933, elevation_m: 1520, city: "Shillong" },
        "neigrihms": { name: "NEIGRIHMS Apex Trauma Center", lat: 25.5996, lng: 91.9392, elevation_m: 1460, city: "Shillong" },
        "shillong_civil": { name: "Shillong Civil Hospital", lat: 25.5725, lng: 91.8828, elevation_m: 1495, city: "Shillong" },
        "nazareth": { name: "Nazareth Hospital (Laitumkhrah)", lat: 25.5682, lng: 91.8955, elevation_m: 1530, city: "Shillong" },
        "woodland": { name: "Woodland Hospital (Dhankheti)", lat: 25.5695, lng: 91.8912, elevation_m: 1515, city: "Shillong" }
    },
    hospitals: {
        "gmch": { name: "GMCH Level 1 Trauma Center", lat: 26.1558, lng: 91.7772, icu: 85, helipad: true },
        "downtown": { name: "Down Town Hospital (Dispur)", lat: 26.1360, lng: 91.7925, icu: 45, helipad: false },
        "excelcare": { name: "Excelcare National Hospital", lat: 26.1265, lng: 91.6872, icu: 35, helipad: false },
        "nongpoh_civil": { name: "Nongpoh Civil Hospital", lat: 25.9015, lng: 91.8790, icu: 12, helipad: false },
        "neigrihms": { name: "NEIGRIHMS Apex Regional Trauma Center", lat: 25.5996, lng: 91.9392, icu: 70, helipad: true },
        "shillong_civil": { name: "Shillong Civil Hospital", lat: 25.5725, lng: 91.8828, icu: 30, helipad: false },
        "nazareth": { name: "Nazareth Hospital", lat: 25.5682, lng: 91.8955, icu: 25, helipad: false },
        "woodland": { name: "Woodland Hospital", lat: 25.5695, lng: 91.8912, icu: 20, helipad: false }
    }
};

// Google Maps Tile Layers (Roadmap lyrs=m, Terrain lyrs=p, Satellite lyrs=s, Hybrid lyrs=y)
const googleTileLayers = {
    roadmap: 'https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
    terrain: 'https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
    satellite: 'https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
    hybrid: 'https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
};

// Initialize Map & Application
document.addEventListener("DOMContentLoaded", () => {
    initLeafletMap();
    populateDropdowns();
    initWebSocket();
    setupEventListeners();
    calculateEmergencySafeRoute();
});

function initLeafletMap() {
    // Center between Guwahati and Shillong
    map = L.map('map', {
        attributionControl: false, // Explicitly disabled attribution per specification
        zoomControl: true
    }).setView([25.8600, 91.8100], 9);

    // Initial Roadmap Layer
    currentTileLayer = L.tileLayer(googleTileLayers.roadmap, {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
    }).addTo(map);

    renderHospitalFacilityMarkers();
}

function switchMapStyle(type, btnElement) {
    document.querySelectorAll('.map-style-btn').forEach(b => b.classList.remove('active'));
    btnElement.classList.add('active');

    map.removeLayer(currentTileLayer);
    currentTileLayer = L.tileLayer(googleTileLayers[type], {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3']
    }).addTo(map);
}

function populateDropdowns() {
    const originSelect = document.getElementById('origin-select');
    const destSelect = document.getElementById('dest-select');

    originSelect.innerHTML = '';
    destSelect.innerHTML = '';

    // Grouping by city
    const nodes = corridorDirectory.nodes;
    
    // Add Guwahati Origin options
    const guwahatiGroup = document.createElement('optgroup');
    guwahatiGroup.label = "Guwahati Hubs";
    
    const hillGroup = document.createElement('optgroup');
    hillGroup.label = "Mid-Corridor Stations";

    const shillongGroup = document.createElement('optgroup');
    shillongGroup.label = "Shillong Hubs";

    Object.keys(nodes).forEach(key => {
        const node = nodes[key];
        const opt = new Option(`${node.name} (${node.elevation_m}m)`, key);
        if (node.city === "Guwahati") {
            guwahatiGroup.appendChild(opt);
        } else if (node.city === "Shillong") {
            shillongGroup.appendChild(opt);
        } else {
            hillGroup.appendChild(opt);
        }
    });

    originSelect.appendChild(guwahatiGroup.cloneNode(true));
    originSelect.appendChild(hillGroup.cloneNode(true));
    originSelect.appendChild(shillongGroup.cloneNode(true));

    // Populate Destination Hospitals
    const destHospGroup = document.createElement('optgroup');
    destHospGroup.label = "Emergency Hospitals & Trauma Centers";
    Object.keys(corridorDirectory.hospitals).forEach(hKey => {
        const h = corridorDirectory.hospitals[hKey];
        destHospGroup.appendChild(new Option(`🏥 ${h.name} (ICU: ${h.icu})`, hKey));
    });

    destSelect.appendChild(destHospGroup);
    destSelect.appendChild(shillongGroup.cloneNode(true));
    destSelect.appendChild(guwahatiGroup.cloneNode(true));

    // Default Selection
    originSelect.value = "paltan_bazar";
    destSelect.value = "neigrihms";
}

function renderHospitalFacilityMarkers() {
    // Clean existing
    hospitalMarkers.forEach(m => map.removeLayer(m));
    hospitalMarkers = [];

    const hospitalIcon = L.divIcon({
        className: 'custom-hosp-marker',
        html: `<div style="background: #0284c7; width: 22px; height: 22px; border-radius: 6px; border: 2px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 10px rgba(0,0,0,0.5); font-size: 11px;">🏥</div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
    });

    Object.keys(corridorDirectory.hospitals).forEach(k => {
        const h = corridorDirectory.hospitals[k];
        const marker = L.marker([h.lat, h.lng], { icon: hospitalIcon }).addTo(map);
        marker.bindPopup(`
            <div class="popup-title">🏥 ${h.name}</div>
            <div class="popup-desc">
                <b>Emergency Capacity:</b> ${h.icu} ICU Beds<br>
                <b>Helipad Evacuation:</b> ${h.helipad ? '✅ Operational' : '❌ Ground Access Only'}<br>
                <b>Coordinates:</b> ${h.lat.toFixed(4)}, ${h.lng.toFixed(4)}
            </div>
        `);
        hospitalMarkers.push(marker);
    });
}

function setupEventListeners() {
    document.getElementById('origin-select').addEventListener('change', calculateEmergencySafeRoute);
    document.getElementById('dest-select').addEventListener('change', calculateEmergencySafeRoute);
    document.getElementById('severity-select').addEventListener('change', calculateEmergencySafeRoute);
    document.getElementById('hazard-condition-select').addEventListener('change', (e) => {
        setSimulatedHazard(e.target.value);
    });
}

// WebSocket Live Telemetry Connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/sensors`;
    
    try {
        websocketClient = new WebSocket(wsUrl);
        websocketClient.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === "SENSOR_UPDATE" || msg.type === "INITIAL_STATE") {
                    updateTelemetryUI(msg.data);
                }
            } catch (err) {
                console.warn("WebSocket parse error:", err);
            }
        };
        websocketClient.onclose = () => {
            setTimeout(initWebSocket, 4000);
        };
    } catch (e) {
        console.log("Offline mode or WebSocket unavailable. Running in client standalone mode.");
    }
}

function setSimulatedHazard(condition) {
    // Update active trigger button state
    document.querySelectorAll('.trigger-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.condition === condition);
    });

    const hazardDropdown = document.getElementById('hazard-condition-select');
    if (hazardDropdown && hazardDropdown.value !== condition) {
        hazardDropdown.value = condition;
    }

    // Call API if live backend available
    fetch('/api/simulate/hazard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ condition: condition })
    })
    .then(r => r.json())
    .then(data => {
        updateTelemetryUI(data);
        calculateEmergencySafeRoute();
    })
    .catch(() => {
        // Standalone client fallback
        fallbackUpdateTelemetry(condition);
        calculateEmergencySafeRoute();
    });
}

function updateTelemetryUI(data) {
    const sensors = data.sensors || {};
    
    // Jorabat Water
    const jorabat = sensors["sensor_jorabat_water"];
    if (jorabat) {
        const el = document.getElementById('gauge-water');
        const box = document.getElementById('box-water');
        el.innerText = `${jorabat.water_level_m} m`;
        if (jorabat.water_level_m >= 4.0) {
            el.style.color = "var(--danger-red)";
            box.className = "telemetry-item alert-red";
        } else if (jorabat.water_level_m >= 2.5) {
            el.style.color = "var(--warning-amber)";
            box.className = "telemetry-item alert-amber";
        } else {
            el.style.color = "var(--text-main)";
            box.className = "telemetry-item";
        }
    }

    // Nongpoh Soil & Rain
    const nongpoh = sensors["sensor_nongpoh_soil"];
    if (nongpoh) {
        const el = document.getElementById('gauge-soil');
        el.innerText = `${nongpoh.soil_moisture_pct}%`;
    }

    // Rain gauge derivation
    const mode = data.simulation_mode || "GREEN";
    const rainEl = document.getElementById('gauge-rain');
    const rainBox = document.getElementById('box-rain');
    if (mode === "RED" || mode === "CLOUDBURST_JORABAT") {
        rainEl.innerText = "124 mm/h";
        rainEl.style.color = "var(--danger-red)";
        rainBox.className = "telemetry-item alert-red";
    } else if (mode === "ORANGE") {
        rainEl.innerText = "48 mm/h";
        rainEl.style.color = "var(--warning-amber)";
        rainBox.className = "telemetry-item alert-amber";
    } else if (mode === "LANDSLIDE_NONGPOH") {
        rainEl.innerText = "88 mm/h";
        rainEl.style.color = "var(--danger-red)";
        rainBox.className = "telemetry-item alert-red";
    } else {
        rainEl.innerText = "4 mm/h";
        rainEl.style.color = "var(--text-main)";
        rainBox.className = "telemetry-item";
    }
}

function fallbackUpdateTelemetry(condition) {
    const mockSensors = {
        sensors: {
            "sensor_jorabat_water": {
                water_level_m: (condition === "RED" || condition === "CLOUDBURST_JORABAT") ? 5.2 : (condition === "ORANGE" ? 3.1 : 1.3)
            },
            "sensor_nongpoh_soil": {
                soil_moisture_pct: (condition === "RED" || condition === "LANDSLIDE_NONGPOH") ? 88.0 : (condition === "ORANGE" ? 64.0 : 32.0)
            }
        },
        simulation_mode: condition
    };
    updateTelemetryUI(mockSensors);
}

// Calculate Disaster Resilient Route
async function calculateEmergencySafeRoute() {
    const originKey = document.getElementById('origin-select').value;
    const destKey = document.getElementById('dest-select').value;
    const condition = document.getElementById('hazard-condition-select').value;
    const severity = document.getElementById('severity-select').value;

    if (originKey === destKey) {
        alert("Origin and Destination cannot be the same!");
        return;
    }

    // Try backend API first
    try {
        const resp = await fetch('/api/route/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                origin: originKey,
                destination: destKey,
                weather_condition: condition,
                emergency_severity: severity
            })
        });
        
        if (resp.ok) {
            const data = await resp.json();
            renderRouteResults(data);
            return;
        }
    } catch (e) {
        // Fallback to client routing
    }

    // Client Standalone Computation Fallback
    renderClientComputedRoute(originKey, destKey, condition);
}

function clearMapRouteLayers() {
    if (activeRouteLayer) map.removeLayer(activeRouteLayer);
    if (blockedRouteLayer) map.removeLayer(blockedRouteLayer);
    if (originMarker) map.removeLayer(originMarker);
    if (destMarker) map.removeLayer(destMarker);
    hazardCircles.forEach(c => map.removeLayer(c));
    hazardCircles = [];
}

function renderRouteResults(data) {
    clearMapRouteLayers();

    const origin = corridorDirectory.nodes[data.origin];
    const dest = corridorDirectory.nodes[data.destination];

    // Origin Icon (Cyan glowing pin)
    const originIcon = L.divIcon({
        html: `<div style="background: #38bdf8; width: 18px; height: 18px; border: 3px solid white; border-radius: 50%; box-shadow: 0 0 12px #38bdf8;"></div>`,
        className: ''
    });

    // Destination Hospital Pin (Red emergency pin)
    const destIcon = L.divIcon({
        html: `<div style="background: #ef4444; width: 22px; height: 22px; border: 3px solid white; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); box-shadow: 0 0 14px #ef4444;"></div>`,
        className: ''
    });

    originMarker = L.marker([origin.lat, origin.lng], { icon: originIcon }).addTo(map).bindPopup(`<b>Start Point:</b> ${origin.name}`);
    destMarker = L.marker([dest.lat, dest.lng], { icon: destIcon }).addTo(map).bindPopup(`<b>Destination:</b> ${dest.name}`);

    const isBypassActive = data.is_bypass_active;
    const aiRoute = data.ai_safe_route;
    const stdRoute = data.standard_route;

    // Render Hazard Warning Zones
    if (data.condition === "RED" || data.condition === "CLOUDBURST_JORABAT" || data.condition === "ORANGE") {
        // Jorabat Inundation Circle
        const jCircle = L.circle([26.0963, 91.8767], {
            color: '#ef4444',
            fillColor: '#ef4444',
            fillOpacity: 0.35,
            weight: 2,
            radius: 4500
        }).addTo(map).bindPopup("<b>🚨 CRITICAL FLOOD SENTRY: JORABAT</b><br>Severe Underpass Inundation (Water Depth: 5.2m)");
        hazardCircles.push(jCircle);
    }

    if (data.condition === "RED" || data.condition === "LANDSLIDE_NONGPOH" || data.condition === "ORANGE") {
        // Nongpoh Landslide Circle
        const nCircle = L.circle([25.9034, 91.8803], {
            color: '#ef4444',
            fillColor: '#ef4444',
            fillOpacity: 0.38,
            weight: 2,
            radius: 8500
        }).addTo(map).bindPopup("<b>⚠️ HIGH RISK LANDSLIDE SCARP: NONGPOH</b><br>Debris Avalanche & Slope Saturation (Slope: 38°)");
        hazardCircles.push(nCircle);
    }

    // Render Blocked Standard Route if bypass active
    if (isBypassActive && stdRoute) {
        const stdCoords = stdRoute.waypoints.map(w => [w.lat, w.lng]);
        blockedRouteLayer = L.polyline(stdCoords, {
            color: '#ef4444',
            weight: 5,
            dashArray: '8, 8',
            opacity: 0.85
        }).addTo(map);
    }

    // Render AI Safe Path (Emerald Green Thick Line #10b981)
    if (aiRoute) {
        const aiCoords = aiRoute.waypoints.map(w => [w.lat, w.lng]);
        activeRouteLayer = L.polyline(aiCoords, {
            color: '#10b981',
            weight: 8,
            opacity: 0.95,
            lineCap: 'round',
            lineJoin: 'round'
        }).addTo(map);

        // Fit map bounds
        const group = new L.featureGroup([originMarker, destMarker, activeRouteLayer]);
        map.fitBounds(group.getBounds().pad(0.2));
    }

    // Update Results Panel
    const resultsPanel = document.getElementById('results-panel');
    resultsPanel.style.display = 'block';

    document.getElementById('res-safety-score').innerText = `${aiRoute ? aiRoute.route_safety_pct : 92.5}%`;
    document.getElementById('res-distance').innerText = `${aiRoute ? aiRoute.total_distance_km : 98.4} km`;
    document.getElementById('res-eta').innerText = `${aiRoute ? aiRoute.estimated_time_minutes : 110} min`;
    document.getElementById('res-status-tag').innerText = isBypassActive ? "🛡️ AI Safe Bypass Active" : "✅ Direct Clear Corridor";
    
    // Render Avoided Hazards
    const hazardsListEl = document.getElementById('avoided-hazards-list');
    hazardsListEl.innerHTML = '';
    
    if (data.avoided_hazards && data.avoided_hazards.length > 0) {
        data.avoided_hazards.forEach(h => {
            const item = document.createElement('div');
            item.className = 'hazard-entry';
            item.innerHTML = `
                <div class="hazard-entry-title">⚠️ ${h.hazard_title}</div>
                <div class="hazard-entry-detail">${h.details}</div>
            `;
            hazardsListEl.appendChild(item);
        });
    } else {
        const item = document.createElement('div');
        item.className = 'hazard-entry';
        item.style.borderColor = 'rgba(16, 185, 129, 0.3)';
        item.style.background = 'rgba(16, 185, 129, 0.08)';
        item.innerHTML = `
            <div class="hazard-entry-title" style="color: #34d399;">✅ All Segments Clear</div>
            <div class="hazard-entry-detail">No critical landslide or flash flood blockages detected.</div>
        `;
        hazardsListEl.appendChild(item);
    }
}

// Standalone Client Route Renderer
function renderClientComputedRoute(originKey, destKey, condition) {
    const origin = corridorDirectory.nodes[originKey];
    const dest = corridorDirectory.nodes[destKey];
    const isRed = (condition === "RED" || condition === "CLOUDBURST_JORABAT" || condition === "LANDSLIDE_NONGPOH");
    
    let path = [];
    let blockedPath = [];
    let avoidedHazards = [];
    let safetyScore = 98.4;
    let distKm = 94.2;

    if (isRed) {
        // Safe mountain bypass path (via Gorchuk - Ranikhamar - Mawlyndep - Mawlai)
        path = [
            { lat: origin.lat, lng: origin.lng },
            { lat: 26.1189, lng: 91.7102 }, // Gorchuk
            { lat: 25.9850, lng: 91.7650 }, // Ranikhamar
            { lat: 25.7011, lng: 91.8210 }, // Mawlyndep Ridge
            { lat: 25.6022, lng: 91.8895 }, // Mawlai
            { lat: dest.lat, lng: dest.lng }
        ];

        // Standard direct blocked path (via Jorabat - Nongpoh NH6)
        blockedPath = [
            { lat: origin.lat, lng: origin.lng },
            { lat: 26.0963, lng: 91.8767 }, // Jorabat
            { lat: 25.9034, lng: 91.8803 }, // Nongpoh
            { lat: 25.6601, lng: 91.9167 }, // Barapani
            { lat: dest.lat, lng: dest.lng }
        ];

        avoidedHazards = [
            { hazard_title: "Avoided: NH-6 Byrnihat-Nongpoh Escarpment", details: "High Landslide Threat (Slope: 38°, Rain: 145mm) on primary highway." },
            { hazard_title: "Avoided: Jorabat Inundation Choke Point", details: "Severe Flash Inundation / Flood (Water Level: 5.2m)." }
        ];
        safetyScore = 89.2;
        distKm = 106.8;
    } else {
        path = [
            { lat: origin.lat, lng: origin.lng },
            { lat: 26.1154, lng: 91.8217 }, // Khanapara
            { lat: 26.0963, lng: 91.8767 }, // Jorabat
            { lat: 25.9034, lng: 91.8803 }, // Nongpoh
            { lat: 25.7533, lng: 91.9056 }, // Umsning
            { lat: 25.6601, lng: 91.9167 }, // Barapani
            { lat: dest.lat, lng: dest.lng }
        ];
        distKm = 96.5;
        safetyScore = 98.8;
    }

    renderRouteResults({
        origin: originKey,
        destination: destKey,
        condition: condition,
        is_bypass_active: isRed,
        ai_safe_route: {
            waypoints: path,
            total_distance_km: distKm,
            route_safety_pct: safetyScore,
            estimated_time_minutes: Math.round((distKm / 46.0) * 60)
        },
        standard_route: isRed ? {
            waypoints: blockedPath,
            total_distance_km: 94.2,
            route_safety_pct: 32.0,
            estimated_time_minutes: 180
        } : null,
        avoided_hazards: avoidedHazards
    });
}
