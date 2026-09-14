/**
 * GPS / Map integration using Leaflet.js + OpenStreetMap tiles (free, no API key).
 * Renders pickup + destination markers, a connecting line, and shows the
 * estimated straight-line distance (matches the backend's Haversine calc).
 */
function renderRideMap(containerId, pickupLat, pickupLng, destLat, destLng, distanceKm) {
    const el = document.getElementById(containerId);
    if (!el) return;

    if (!pickupLat || !pickupLng || !destLat || !destLng) {
        el.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 text-muted small">' +
            'Map preview unavailable (location coordinates not resolved).</div>';
        return;
    }

    const map = L.map(containerId).setView([pickupLat, pickupLng], 11);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 18,
    }).addTo(map);

    const pickupMarker = L.marker([pickupLat, pickupLng]).addTo(map).bindPopup('Pickup');
    const destMarker = L.marker([destLat, destLng]).addTo(map).bindPopup('Destination');

    const line = L.polyline([[pickupLat, pickupLng], [destLat, destLng]], {
        color: '#1f6f5c', weight: 4, dashArray: '6 8',
    }).addTo(map);

    map.fitBounds(line.getBounds(), { padding: [30, 30] });

    if (distanceKm) {
        const label = document.getElementById(containerId + '-distance');
        if (label) label.innerText = `Estimated distance: ${distanceKm} km`;
    }
}

/**
 * Uses the browser's Geolocation API to auto-fill a "current location"
 * input field with reverse-geocoded coordinates (lat,lng passed to backend
 * for geocoding lookups happens server-side; here we just capture coords).
 */
function useMyLocation(latFieldId, lngFieldId, statusElId) {
    const statusEl = document.getElementById(statusElId);
    if (!navigator.geolocation) {
        if (statusEl) statusEl.innerText = 'Geolocation is not supported by your browser.';
        return;
    }
    if (statusEl) statusEl.innerText = 'Locating you...';
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            document.getElementById(latFieldId).value = pos.coords.latitude;
            document.getElementById(lngFieldId).value = pos.coords.longitude;
            if (statusEl) statusEl.innerText = `Location captured (±${Math.round(pos.coords.accuracy)}m accuracy).`;
        },
        (err) => {
            if (statusEl) statusEl.innerText = 'Could not fetch location: ' + err.message;
        }
    );
}
