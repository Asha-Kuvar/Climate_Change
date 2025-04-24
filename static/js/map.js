let map;
let tileLayer;

export function initMap() {
    map = L.map('map').setView([20, 0], 2);
    updateMapTileLayer();
}

export function updateMapTileLayer() {
    if (tileLayer) tileLayer.remove();
    const isDark = document.body.classList.contains('dark-theme');
    const tileUrl = isDark
        ? 'https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=YOUR_MAPBOX_TOKEN'
        : 'https://api.mapbox.com/styles/v1/mapbox/light-v10/tiles/{z}/{x}/{y}?access_token=YOUR_MAPBOX_TOKEN';
    tileLayer = L.tileLayer(tileUrl, {
        maxZoom: 18,
        attribution: '© Mapbox © OpenStreetMap'
    }).addTo(map);

    // Add satellite imagery for deforestation
    L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=YOUR_MAPBOX_TOKEN', {
        opacity: 0.5,
        maxZoom: 18
    }).addTo(map);
}