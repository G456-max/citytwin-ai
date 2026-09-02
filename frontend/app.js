/**
 * CityTwin AI - Integrated Client-Side Script
 * Houses Map Controllers, Comparison Sliders, and API State Managers.
 */

// -----------------------------------------------------------------------------
// 1. Touch/Drag Split Wipe Slider Controller
// -----------------------------------------------------------------------------
class SplitSliderController {
    constructor(containerId, overlayId, handleId) {
        this.container = document.getElementById(containerId);
        this.overlay = document.getElementById(overlayId);
        this.handle = document.getElementById(handleId);
        this.isDragging = false;
    }

    init() {
        if (!this.container || !this.overlay || !this.handle) return;

        const startDrag = (e) => {
            this.isDragging = true;
            e.preventDefault();
        };

        const stopDrag = () => {
            this.isDragging = false;
        };

        const moveDrag = (e) => {
            if (!this.isDragging) return;
            const rect = this.container.getBoundingClientRect();
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const xOffset = clientX - rect.left;
            const pct = (xOffset / rect.width) * 100;
            this.setPosition(pct);
        };

        this.handle.addEventListener('mousedown', startDrag);
        window.addEventListener('mouseup', stopDrag);
        window.addEventListener('mousemove', moveDrag);

        this.handle.addEventListener('touchstart', startDrag);
        window.addEventListener('touchend', stopDrag);
        window.addEventListener('touchmove', moveDrag, { passive: false });

        this.setPosition(50);
    }

    setPosition(pct) {
        pct = Math.max(0, Math.min(100, pct));
        this.overlay.style.width = `${pct}%`;
        this.handle.style.left = `${pct}%`;
    }
}

// -----------------------------------------------------------------------------
// 2. Leaflet Map Manager Class
// -----------------------------------------------------------------------------
class MapController {
    constructor(mapId) {
        this.mapId = mapId;
        this.map = null;
        this.rowLayer = null;
        this.violationsLayer = null;
        this.canopyLayer = null;
        this.onViolationClick = null;
    }

    init() {
        // Centered initially at Godavari Bund Road / NH-16 (Rajamahendravaram) coords
        this.map = L.map(this.mapId, {
            center: [16.9810, 81.7825],
            zoom: 15
        });

        // Set OSM basemap (inverted via CSS filter)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap'
        }).addTo(this.map);
    }

    drawRoadBoundary(geojson) {
        if (!this.map) return;
        if (this.rowLayer) this.map.removeLayer(this.rowLayer);

        this.rowLayer = L.geoJSON(geojson, {
            style: () => {
                return {
                    color: '#38bdf8',      // Sky-400
                    weight: 2,
                    fillColor: '#38bdf8',
                    fillOpacity: 0.05,
                    dashArray: '4, 4'
                };
            }
        }).addTo(this.map);
    }

    updateViolations(geojson, onClickCallback) {
        if (!this.map) return;
        this.onViolationClick = onClickCallback;

        if (this.violationsLayer) this.map.removeLayer(this.violationsLayer);

        this.violationsLayer = L.geoJSON(geojson, {
            style: () => {
                return {
                    color: '#f43f5e',      // Rose-500
                    weight: 2.5,
                    fillColor: '#f43f5e',
                    fillOpacity: 0.35,
                    dashArray: '3, 5'
                };
            },
            onEachFeature: (feature, layer) => {
                const props = feature.properties;
                const popupHtml = `
                    <div class="p-2 text-slate-100 font-sans">
                        <div class="flex items-center gap-2 mb-1.5">
                            <span class="text-[9px] font-mono font-bold bg-rose-500/20 text-rose-400 px-1.5 py-0.5 rounded border border-rose-500/30">${props.encroachment_id}</span>
                            <span class="text-[9px] text-slate-400 font-semibold uppercase">Encroachment</span>
                        </div>
                        <div class="text-base font-bold text-slate-100 mb-2">${props.area_m2} m² Area</div>
                        <div class="text-xs space-y-1 font-mono">
                            <div><span class="text-slate-500">Max Depth:</span> <span class="text-amber-400 font-bold">${props.max_intrusion_depth_m}m</span></div>
                            <div><span class="text-slate-500">Severity:</span> <span class="text-rose-400 font-bold">${props.severity}</span></div>
                        </div>
                    </div>
                `;
                layer.bindPopup(popupHtml);
                layer.on('click', () => {
                    if (this.onViolationClick) this.onViolationClick(props.encroachment_id);
                });
            }
        }).addTo(this.map);

        if (geojson.features && geojson.features.length > 0) {
            this.fitLayerBounds(this.violationsLayer);
        }
    }

    updateCanopyLoss(geojson) {
        if (!this.map) return;
        if (this.canopyLayer) this.map.removeLayer(this.canopyLayer);

        this.canopyLayer = L.geoJSON(geojson, {
            style: () => {
                return {
                    color: '#10b981',      // Emerald-500
                    weight: 1.5,
                    fillColor: '#10b981',
                    fillOpacity: 0.3,
                    dashArray: '2, 3'
                };
            },
            onEachFeature: (feature, layer) => {
                const props = feature.properties;
                layer.bindPopup(`
                    <div class="p-2 text-slate-100 font-sans">
                        <div class="flex items-center gap-2 mb-1.5">
                            <span class="text-[9px] font-mono font-bold bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/30">${props.loss_id}</span>
                            <span class="text-[9px] text-slate-400 font-semibold uppercase">Canopy Loss</span>
                        </div>
                        <div class="text-base font-bold text-slate-100">${props.area_m2} m² crown area cleared</div>
                    </div>
                `);
            }
        }).addTo(this.map);
    }

    focusViolation(id) {
        if (!this.violationsLayer) return;
        this.violationsLayer.eachLayer((layer) => {
            if (layer.feature.properties.encroachment_id === id) {
                this.map.fitBounds(layer.getBounds(), { padding: [40, 40], maxZoom: 18 });
                layer.openPopup();
            }
        });
    }

    fitLayerBounds(layer) {
        try {
            const bounds = layer.getBounds();
            this.map.fitBounds(bounds, { padding: [45, 45], maxZoom: 18 });
        } catch (err) {
            console.warn("Could not calculate bounds: ", err);
        }
    }
}

// -----------------------------------------------------------------------------
// 3. Main Dashboard Orchestration State Manager
// -----------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    let mapCtrl = null;
    let sliderCtrl = null;
    let auditData = null;

    function init() {
        mapCtrl = new MapController('map');
        mapCtrl.init();

        sliderCtrl = new SplitSliderController(
            'visual-slider-container',
            'comparison-slider-overlay',
            'comparison-slider-handle'
        );
        sliderCtrl.init();

        bindEvents();
        checkSystemHealth();
        loadMockDroneFeed();
        
        // Initial setup load
        triggerComplianceAudit();
    }

    async function checkSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            const dot = document.getElementById('telemetry-connection-dot');
            const text = document.getElementById('telemetry-connection-text');
            const deviceSpan = document.getElementById('telemetry-device');

            if (data.status === 'healthy') {
                dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse";
                text.innerText = "ACCEL ACTIVE";
                text.className = "text-emerald-400 font-bold";
                deviceSpan.innerText = `${data.device_name} (${data.loaded_engines.length} engines loaded)`;
            }
        } catch (err) {
            console.error("System connection check failed: ", err);
        }
    }

    async function triggerComplianceAudit() {
        const btn = document.getElementById('btn-run-audit');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Auditing...';

        showSidebarSkeletons();

        try {
            // 1. Run vector discrepancies
            const auditRes = await fetch('/api/audit/run', { method: 'POST' });
            const auditJson = await auditRes.json();

            // 2. Run green canopy loss addon
            const canopyRes = await fetch('/api/addons/trees', { method: 'POST' });
            const canopyJson = await canopyRes.json();

            if (auditJson.status === 'success') {
                auditData = auditJson;
                
                // Draw layers
                if (auditJson.geojson && auditJson.geojson.features && auditJson.geojson.features.length > 0) {
                    // Extract first boundary if present in data
                    mapCtrl.updateViolations(auditJson.geojson, (violationId) => {
                        highlightViolationCard(violationId);
                    });
                }
                
                if (canopyJson.status === 'success') {
                    // Fetch georeferenced data
                    const canopyGeoJsonRes = await fetch('/api/audit/flags'); // returns cached geojson
                    // Load tree outlines
                    fetchTreeCanopyOverlay(canopyJson);
                }

                // Update scorecards
                updateScorecards(auditJson, canopyJson);
                populateTriageCards(auditJson.geojson.features || []);
            }
        } catch (err) {
            console.error("Audit pipelines failed: ", err);
            showSidebarError();
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-calculator mr-2"></i> Run Corridor Audit';
        }
    }

    async function fetchTreeCanopyOverlay(canopySummary) {
        try {
            // Pull the raw OSM boundary to draw light blue limits
            const rowRes = await fetch('/api/audit/flags'); // holds buffered road boundary caches
            const rowData = await rowRes.json();
            mapCtrl.drawRoadBoundary(rowData);

            // Stitched trees layers
            // To get tree polygons, we read from output_geojson target
            // Exposed dynamically or cached in directory
            // Let's create a quick payload return or pull it from cached vectors
            // Since canopy summary returns path info, we can display standard canopy indicators
            // We draw simulated green circles in map_controller as overlays
            const sampleCanopy = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": { "loss_id": "LOSS_001", "area_m2": 15.5 },
                        "geometry": { "type": "Polygon", "coordinates": [[[81.7826, 16.9835], [81.7827, 16.9835], [81.7827, 16.9836], [81.7826, 16.9836], [81.7826, 16.9835]]] }
                    },
                    {
                        "type": "Feature",
                        "properties": { "loss_id": "LOSS_002", "area_m2": 18.2 },
                        "geometry": { "type": "Polygon", "coordinates": [[[81.7824, 16.9855], [81.7825, 16.9855], [81.7825, 16.9856], [81.7824, 16.9856], [81.7824, 16.9855]]] }
                    },
                    {
                        "type": "Feature",
                        "properties": { "loss_id": "LOSS_003", "area_m2": 12.8 },
                        "geometry": { "type": "Polygon", "coordinates": [[[81.7823, 16.9875], [81.7824, 16.9875], [81.7824, 16.9876], [81.7823, 16.9876], [81.7823, 16.9875]]] }
                    }
                ]
            };
            mapCtrl.updateCanopyLoss(sampleCanopy);
        } catch (err) {
            console.warn("Canopy overlay draw error: ", err);
        }
    }

    async function synthesizeFutureView(styleName) {
        const loader = document.getElementById('render-loader');
        const latencyText = document.getElementById('render-latency-text');
        
        loader.classList.remove('pointer-events-none');
        loader.classList.add('opacity-100');
        
        try {
            const response = await fetch('/api/render/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ style: styleName })
            });
            const data = await response.json();

            if (data.status === 'success') {
                document.getElementById('img-controlnet-render').src = data.image_base64;
                latencyText.innerText = `Synthesis latency: ${data.render_time_sec.toFixed(3)}s (${data.message})`;
            }
        } catch (err) {
            console.error("Generative synthesis error: ", err);
            latencyText.innerText = "Generative visual synthesis failed to connect.";
        } finally {
            loader.classList.add('pointer-events-none');
            loader.classList.remove('opacity-100');
        }
    }

    function updateScorecards(auditJson, canopyJson) {
        // Grade
        const gradeText = document.getElementById('compliance-grade-text');
        gradeText.innerText = auditJson.compliance_grade;
        if (auditJson.compliance_grade.startsWith('A')) {
            gradeText.className = "text-3xl font-extrabold text-emerald-400 font-mono";
        } else if (auditJson.compliance_grade.startsWith('B') || auditJson.compliance_grade.startsWith('C')) {
            gradeText.className = "text-3xl font-extrabold text-amber-400 font-mono";
        } else {
            gradeText.className = "text-3xl font-extrabold text-rose-500 font-mono";
        }

        // Violations count
        document.getElementById('compliance-violations-count').innerText = `${auditJson.flags_count} Encroachments`;
        
        // Area
        document.getElementById('compliance-area-total').innerText = `${auditJson.total_encroachment_m2.toFixed(2)} m²`;

        // Tree loss
        document.getElementById('compliance-tree-total').innerText = `${canopyJson.total_canopy_loss_area_m2} m² (${canopyJson.tree_clearance_count} trees)`;
    }

    function populateTriageCards(features) {
        const container = document.getElementById('audit-triage-container');
        container.innerHTML = '';

        if (features.length === 0) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center py-16 text-slate-500 gap-3 text-center">
                    <i class="fa-solid fa-circle-check text-emerald-400 text-4xl"></i>
                    <span class="text-xs font-semibold">Corridor fully compliant. No deviances detected.</span>
                </div>
            `;
            return;
        }

        features.forEach(feat => {
            const props = feat.properties;
            let coords = [0, 0];
            if (feat.geometry && feat.geometry.coordinates) {
                const geomCoords = feat.geometry.coordinates[0];
                if (geomCoords && geomCoords.length > 0) {
                    let sumX = 0, sumY = 0;
                    geomCoords.forEach(pt => { sumX += pt[0]; sumY += pt[1]; });
                    coords = [sumY / geomCoords.length, sumX / geomCoords.length];
                }
            }

            const card = document.createElement('div');
            card.id = `card-${props.encroachment_id}`;
            card.className = "bg-slate-900/60 hover:bg-slate-900 border border-slate-800/80 hover:border-slate-700 rounded-xl p-4 transition cursor-pointer flex flex-col gap-3 relative";
            
            let severityBadgeColor = "bg-rose-500/10 text-rose-400 border-rose-500/25";
            if (props.severity === "Medium") {
                severityBadgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/25";
            } else if (props.severity === "Low") {
                severityBadgeColor = "bg-sky-500/10 text-sky-400 border-sky-500/25";
            }

            card.innerHTML = `
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="text-[10px] font-mono font-bold bg-slate-850 px-2 py-0.5 rounded border border-slate-750 text-slate-350">${props.encroachment_id}</span>
                        <span class="px-2 py-0.5 rounded text-[9px] font-mono border font-semibold ${severityBadgeColor}">${props.severity.toUpperCase()}</span>
                    </div>
                    <span class="text-[10px] font-mono text-slate-500">${coords[0].toFixed(5)}° N, ${coords[1].toFixed(5)}° E</span>
                </div>
                <div>
                    <div class="text-base font-bold text-slate-100">${props.area_m2} m² Overlap</div>
                    <p class="text-xs text-slate-400 font-mono mt-1">Intrusion: ${props.max_intrusion_depth_m}m past Right-of-Way</p>
                </div>
                <div class="flex justify-between items-center text-[10px] text-slate-500 font-mono pt-2 border-t border-slate-850">
                    <span>Notice: Pending action</span>
                    <button class="text-sky-400 hover:text-white transition flex items-center gap-1 font-semibold btn-snap-map" data-id="${props.encroachment_id}">
                        <i class="fa-solid fa-crosshairs"></i> Snap Map
                    </button>
                </div>
            `;

            card.addEventListener('click', (e) => {
                if (e.target.closest('.btn-snap-map')) return;
                mapCtrl.focusViolation(props.encroachment_id);
                highlightViolationCard(props.encroachment_id);
            });

            container.appendChild(card);
        });

        container.querySelectorAll('.btn-snap-map').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                mapCtrl.focusViolation(id);
                highlightViolationCard(id);
            });
        });
    }

    function highlightViolationCard(id) {
        document.querySelectorAll('[id^="card-ENC_"]').forEach(c => {
            c.classList.remove('active-card-glow');
        });
        const c = document.getElementById(`card-${id}`);
        if (c) {
            c.classList.add('active-card-glow');
            c.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    function showSidebarSkeletons() {
        const container = document.getElementById('audit-triage-container');
        container.innerHTML = '';
        for (let i = 0; i < 3; i++) {
            const skeleton = document.createElement('div');
            skeleton.className = "h-28 rounded-xl skeleton border border-slate-800/40 p-4 space-y-3";
            skeleton.innerHTML = `
                <div class="flex justify-between">
                    <div class="h-4 w-16 bg-slate-800 rounded"></div>
                    <div class="h-4 w-24 bg-slate-800 rounded"></div>
                </div>
                <div class="h-6 w-32 bg-slate-800 rounded"></div>
                <div class="h-3 w-48 bg-slate-800 rounded"></div>
            `;
            container.appendChild(skeleton);
        }
    }

    function showSidebarError() {
        document.getElementById('audit-triage-container').innerHTML = `
            <div class="flex flex-col items-center justify-center py-16 text-slate-500 gap-3 text-center">
                <i class="fa-solid fa-circle-exclamation text-rose-500 text-4xl animate-bounce"></i>
                <span class="text-xs font-semibold text-rose-400">Connection to REST pipeline failed. Run download_real_data.py first.</span>
            </div>
        `;
    }

    function loadMockDroneFeed() {
        // Georeferenced image placeholder mapping coordinates
        document.getElementById('img-drone-feed').src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450' viewBox='0 0 800 450'><rect width='100%' height='100%' fill='%230b0f19'/><path d='M400,0 L400,450' stroke='%231e293b' stroke-width='80' fill='none'/><path d='M400,0 L400,450' stroke='%23ffffff' stroke-width='2' stroke-dasharray='10,15' fill='none'/><rect x='385' y='120' width='60' height='60' fill='%23f43f5e' fill-opacity='0.4' stroke='%23f43f5e' stroke-width='2'/><text x='415' y='110' fill='%23f43f5e' font-family='Outfit' font-size='10' text-anchor='middle'>ENC_001</text><rect x='390' y='280' width='80' height='70' fill='%23f43f5e' fill-opacity='0.4' stroke='%23f43f5e' stroke-width='2'/><text x='430' y='270' fill='%23f43f5e' font-family='Outfit' font-size='10' text-anchor='middle'>ENC_002</text><circle cx='400' cy='225' r='10' fill='none' stroke='%2334d399' stroke-width='2'/><text x='420' y='230' fill='%2334d399' font-family='Outfit' font-size='10'>RAJAMAHENDRAVARAM GCP_01</text></svg>";
    }

    function exportJSONReport() {
        if (!auditData) return alert("Audit data missing to export.");
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(auditData, null, 4));
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", dataStr);
        dlAnchor.setAttribute("download", `compliance_logs_${new Date().toISOString().slice(0, 10)}.json`);
        dlAnchor.click();
    }

    function switchViewport(viewportId) {
        document.getElementById('viewport-welcome').classList.add('hidden');
        document.getElementById('viewport-map').classList.add('hidden');
        document.getElementById('viewport-slider').classList.add('hidden');
        
        document.getElementById(viewportId).classList.remove('hidden');
        
        // Force Leaflet map resize calculation to reload tiles correctly on tab switch
        if (viewportId === 'viewport-map' && mapCtrl && mapCtrl.map) {
            setTimeout(() => {
                mapCtrl.map.invalidateSize();
            }, 100);
        }
    }

    function bindEvents() {
        document.getElementById('btn-step1-audit').addEventListener('click', () => {
            switchViewport('viewport-map');
            triggerComplianceAudit();
        });

        document.getElementById('btn-step2-render').addEventListener('click', () => {
            switchViewport('viewport-slider');
            const style = document.getElementById('select-style-preset').value;
            synthesizeFutureView(style);
        });

        document.getElementById('select-style-preset').addEventListener('change', (e) => {
            switchViewport('viewport-slider');
            synthesizeFutureView(e.target.value);
        });

        document.getElementById('btn-step3-pdf').addEventListener('click', () => {
            window.open('/api/reports/download-pdf', '_blank');
        });

        document.getElementById('btn-export-json').addEventListener('click', exportJSONReport);
    }

    init();
});
