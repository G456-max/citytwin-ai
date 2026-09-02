/**
 * Leaflet.js Map controller for displaying digital twin assets and violations.
 */
class MapController {
    constructor(mapId) {
        this.mapId = mapId;
        this.map = null;
        this.violationsLayer = null;
        this.rowLayer = null;
        this.onViolationClickCallback = null;
    }

    init() {
        // Initialize map centered at target coordinate
        this.map = L.map(this.mapId, {
            center: [16.9810, 81.7825],
            zoom: 15,
            zoomControl: true
        });

        // Set up osm tile base layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }

    updateViolations(geojson, onClickCallback) {
        if (!this.map) return;
        this.onViolationClickCallback = onClickCallback;

        // Clear existing violations from map
        if (this.violationsLayer) {
            this.map.removeLayer(this.violationsLayer);
        }

        // Draw new red violation layers
        this.violationsLayer = L.geoJSON(geojson, {
            style: () => {
                return {
                    color: '#f43f5e',      // Rose-500 (brand-red)
                    weight: 2.5,
                    fillColor: '#f43f5e',
                    fillOpacity: 0.35,
                    dashArray: '3, 5'
                };
            },
            onEachFeature: (feature, layer) => {
                const props = feature.properties;
                const popupContent = `
                    <div class="p-2 text-slate-100 font-sans">
                        <div class="flex items-center gap-2 mb-1.5">
                            <span class="text-[10px] font-mono font-bold bg-rose-500/25 text-rose-500 px-1.5 py-0.5 rounded border border-rose-500/30">${props.encroachment_id}</span>
                            <span class="text-[10px] text-slate-400 font-semibold">Corridor Intrusion</span>
                        </div>
                        <div class="text-base font-bold text-slate-100 mb-2">${props.area_m2} m² Area</div>
                        <div class="text-xs space-y-1 font-mono">
                            <div><span class="text-slate-500">Max Depth:</span> <span class="text-amber-400 font-bold">${props.max_intrusion_depth_m}m</span></div>
                            <div><span class="text-slate-500">Confidence:</span> <span class="text-sky-400">${(props.confidence * 100).toFixed(0)}%</span></div>
                            <div><span class="text-slate-500">Severity:</span> <span class="text-rose-400 font-bold">${props.severity}</span></div>
                        </div>
                    </div>
                `;
                layer.bindPopup(popupContent);

                layer.on('click', () => {
                    if (this.onViolationClickCallback) {
                        this.onViolationClickCallback(props.encroachment_id);
                    }
                });
            }
        }).addTo(this.map);

        // Zoom map to show all violations if layer holds geometry
        if (geojson.features && geojson.features.length > 0) {
            try {
                const bounds = this.violationsLayer.getBounds();
                this.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 18 });
            } catch (err) {
                console.warn("Could not calculate bounds for layers: ", err);
            }
        }
    }

    focusViolation(id) {
        if (!this.violationsLayer || !this.map) return;

        this.violationsLayer.eachLayer((layer) => {
            if (layer.feature.properties.encroachment_id === id) {
                this.map.fitBounds(layer.getBounds(), { padding: [40, 40], maxZoom: 18 });
                layer.openPopup();
            }
        });
    }
}

// Bind to window
window.MapController = MapController;
