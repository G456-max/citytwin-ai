/**
 * Unified application state manager and API client for CityTwin AI.
 */
document.addEventListener('DOMContentLoaded', () => {
    // State indicators
    let mapCtrl = null;
    let sliderCtrl = null;
    let activeViolationId = null;
    let auditData = null;

    // -------------------------------------------------------------------------
    // 1. App Startup & Initialization
    // -------------------------------------------------------------------------
    function init() {
        // Init Leaflet map
        mapCtrl = new MapController('map');
        mapCtrl.init();

        // Init Compare Slider
        sliderCtrl = new SplitSliderController(
            'visual-slider-container',
            'comparison-slider-overlay',
            'comparison-slider-handle'
        );
        sliderCtrl.init();

        // Bind event listeners
        bindEvents();

        // Check backend diagnostics health
        checkSystemHealth();

        // Preload baseline images
        loadMockDroneFeed();
        
        // Initial audit load
        triggerComplianceAudit();
    }

    // -------------------------------------------------------------------------
    // 2. Health & Diagnostics Checks
    // -------------------------------------------------------------------------
    async function checkSystemHealth() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            
            const dot = document.getElementById('telemetry-connection-dot');
            const text = document.getElementById('telemetry-connection-text');
            const deviceSpan = document.getElementById('telemetry-device');

            if (data.status === 'healthy') {
                dot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse";
                text.innerText = "CONNECTED";
                text.className = "text-emerald-400";
                
                // Set hardware info
                deviceSpan.innerText = `${data.device_name} (Loaded: ${data.loaded_engines.length} engines)`;
            }
        } catch (err) {
            console.error("System health check failed: ", err);
            const dot = document.getElementById('telemetry-connection-dot');
            const text = document.getElementById('telemetry-connection-text');
            
            dot.className = "w-2.5 h-2.5 rounded-full bg-rose-500";
            text.innerText = "OFFLINE";
            text.className = "text-rose-500";
        }
    }

    // -------------------------------------------------------------------------
    // 3. API Execution Routes
    // -------------------------------------------------------------------------
    async function triggerComplianceAudit() {
        const btn = document.getElementById('btn-run-audit');
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Auditing...';

        // Load sidebar skeletons
        showSidebarSkeletons();

        try {
            const response = await fetch('/api/audit/real', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const data = await response.json();

            if (data.status === 'success') {
                auditData = data;
                
                // Update map polygons
                mapCtrl.updateViolations(data.geojson, (violationId) => {
                    highlightViolationCard(violationId);
                });

                // Render metrics and card listings
                updateComplianceMetrics(data);
                populateTriageCards(data.geojson.features || []);
            }
        } catch (err) {
            console.error("Compliance audit execution failed: ", err);
            showSidebarError();
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-shield-halved mr-2"></i> Run Discrepancy Audit';
        }
    }

    async function synthesizeFutureView(styleName) {
        const loader = document.getElementById('render-loader');
        const latencyText = document.getElementById('render-latency-text');
        
        loader.classList.remove('pointer-events-none');
        loader.classList.add('opacity-100');
        
        try {
            const response = await fetch('/api/render/real', {
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
            console.error("Generative visual synthesis failed: ", err);
            latencyText.innerText = "Visual synthesis failed to connect.";
        } finally {
            loader.classList.add('pointer-events-none');
            loader.classList.remove('opacity-100');
        }
    }

    // -------------------------------------------------------------------------
    // 4. UI Rendering Helpers
    // -------------------------------------------------------------------------
    function updateComplianceMetrics(data) {
        // Grade parsing
        const gradeText = document.getElementById('compliance-grade-text');
        gradeText.innerText = data.compliance_grade;
        
        // Severity color grade mapping
        if (data.compliance_grade.startsWith('A')) {
            gradeText.className = "text-3xl font-extrabold text-emerald-400 font-mono";
        } else if (data.compliance_grade.startsWith('B') || data.compliance_grade.startsWith('C')) {
            gradeText.className = "text-3xl font-extrabold text-amber-400 font-mono";
        } else {
            gradeText.className = "text-3xl font-extrabold text-rose-500 font-mono";
        }

        // Flags Count
        const countText = document.getElementById('compliance-violations-count');
        countText.innerText = `${data.flags_count} Violations`;

        // Total Area
        const areaText = document.getElementById('compliance-area-total');
        areaText.innerText = `${data.total_encroachment_m2.toFixed(2)} m²`;
    }

    function populateTriageCards(features) {
        const container = document.getElementById('audit-triage-container');
        container.innerHTML = '';

        if (features.length === 0) {
            container.innerHTML = `
                <div class="flex flex-col items-center justify-center py-16 text-slate-500 gap-3 text-center">
                    <i class="fa-solid fa-circle-check text-emerald-400 text-4xl"></i>
                    <span class="text-xs font-semibold">Corridor fully compliant. No encroachments detected.</span>
                </div>
            `;
            return;
        }

        features.forEach(feat => {
            const props = feat.properties;
            
            // Map coordinates center coordinates if geometry is polygon
            let centroid = [0, 0];
            if (feat.geometry && feat.geometry.coordinates) {
                // Simplified bbox centroid estimate for display
                const coords = feat.geometry.coordinates[0];
                if (coords && coords.length > 0) {
                    let sumX = 0, sumY = 0;
                    coords.forEach(pt => {
                        sumX += pt[0];
                        sumY += pt[1];
                    });
                    centroid = [sumY / coords.length, sumX / coords.length];
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
                        <span class="text-[10px] font-mono font-bold bg-slate-850 px-2 py-0.5 rounded border border-slate-750 text-slate-300">${props.encroachment_id}</span>
                        <span class="px-2 py-0.5 rounded text-[9px] font-mono border font-semibold ${severityBadgeColor}">${props.severity.toUpperCase()}</span>
                    </div>
                    <span class="text-[10px] font-mono text-slate-500">${centroid[0].toFixed(5)}° N, ${centroid[1].toFixed(5)}° E</span>
                </div>
                <div>
                    <div class="text-base font-bold text-slate-100">${props.area_m2} m² Encroached</div>
                    <p class="text-xs text-slate-400 font-mono mt-1">Linear Intrusion depth: ${props.max_intrusion_depth_m}m past boundary edge</p>
                </div>
                <div class="flex justify-between items-center text-[10px] text-slate-500 font-mono pt-2 border-t border-slate-850">
                    <span>Status: Notice Issued</span>
                    <button class="text-sky-400 hover:text-white transition flex items-center gap-1 font-semibold btn-snap-map" data-id="${props.encroachment_id}">
                        <i class="fa-solid fa-location-crosshairs"></i> Snap Map
                    </button>
                </div>
            `;

            // Clicking card focuses map
            card.addEventListener('click', (e) => {
                if (e.target.closest('.btn-snap-map')) return; // handled by button
                mapCtrl.focusViolation(props.encroachment_id);
                highlightViolationCard(props.encroachment_id);
            });

            container.appendChild(card);
        });

        // Bind map buttons individually
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
        // Clear active borders
        document.querySelectorAll('[id^="card-ENC_"]').forEach(c => {
            c.classList.remove('card-alert-active');
        });

        const activeCard = document.getElementById(`card-${id}`);
        if (activeCard) {
            activeCard.classList.add('card-alert-active');
            activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        activeViolationId = id;
    }

    // Loader display components
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
        const container = document.getElementById('audit-triage-container');
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16 text-slate-500 gap-3 text-center">
                <i class="fa-solid fa-circle-exclamation text-rose-500 text-4xl animate-bounce"></i>
                <span class="text-xs font-semibold text-rose-400">Connection to REST audit pipeline failed. Check server configuration.</span>
            </div>
        `;
    }

    function loadMockDroneFeed() {
        // Mock ortho raster view
        document.getElementById('img-drone-feed').src = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='800' height='450' viewBox='0 0 800 450'><rect width='100%' height='100%' fill='%230f172a'/><path d='M-100,550 L900,-100' stroke='%23334155' stroke-width='90' fill='none'/><path d='M-100,550 L900,-100' stroke='%23ffffff' stroke-width='3' stroke-dasharray='10,15' fill='none'/><rect x='410' y='140' width='80' height='100' fill='%23f43f5e' fill-opacity='0.4' stroke='%23f43f5e' stroke-width='2'/><text x='450' y='130' fill='%23f43f5e' font-family='Outfit' font-size='10' text-anchor='middle'>ENC_002</text><rect x='280' y='280' width='100' height='100' fill='%23f43f5e' fill-opacity='0.4' stroke='%23f43f5e' stroke-width='2'/><text x='330' y='270' fill='%23f43f5e' font-family='Outfit' font-size='10' text-anchor='middle'>ENC_001</text><rect x='600' y='60' width='80' height='70' fill='%231e293b' stroke='%23475569' stroke-width='2'/><text x='640' y='50' fill='%2394a3b8' font-family='Outfit' font-size='10' text-anchor='middle'>COMPLIANT</text><circle cx='400' cy='225' r='10' fill='none' stroke='%2334d399' stroke-width='2'/><line x1='400' y1='210' x2='400' y2='240' stroke='%2334d399' stroke-width='1.5'/><line x1='385' y1='225' x2='415' y2='225' stroke='%2334d399' stroke-width='1.5'/><text x='420' y='210' fill='%2334d399' font-family='Outfit' font-size='10'>DRONE GCP_01</text></svg>";
    }

    // -------------------------------------------------------------------------
    // 5. Exporter & Event Listeners
    // -------------------------------------------------------------------------
    function exportJSONReport() {
        if (!auditData) {
            alert("No audit logs loaded to export.");
            return;
        }

        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(auditData, null, 4));
        const dlAnchorElem = document.createElement('a');
        dlAnchorElem.setAttribute("href", dataStr);
        dlAnchorElem.setAttribute("download", `citytwin_audit_report_${new Date().toISOString().slice(0, 10)}.json`);
        dlAnchorElem.click();
    }

    function bindEvents() {
        // Discrepancy button
        document.getElementById('btn-run-audit').addEventListener('click', triggerComplianceAudit);

        // Synthesis controls
        document.getElementById('btn-synthesize-cad').addEventListener('click', () => {
            const style = document.getElementById('select-style-preset').value;
            synthesizeFutureView(style);
        });

        document.getElementById('select-style-preset').addEventListener('change', (e) => {
            synthesizeFutureView(e.target.value);
        });

        // JSON Exporter
        document.getElementById('btn-export-json').addEventListener('click', exportJSONReport);
    }

    // Launch app
    init();
});
