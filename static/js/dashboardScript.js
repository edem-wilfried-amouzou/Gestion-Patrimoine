// dashboardScript.js — Leaflet direct (sans iframe Folium)
// Fixes : clics carte, icônes propres, itinéraire multi-points, navigation implémentée

(function () {
    // ==================== ÉTAT GLOBAL ====================
    let map = null;
    let markersLayer = null;
    let othersLayer = null;
    let itineraryLayer = null;
    let navigationLayer = null;
    let currentMode = null;
    let addTempMarker = null;
    let navStartMarker = null;
    let navStartLatLng = null;
    let othersVisible = true;

    // ==================== INITIALISATION CARTE ====================
    document.addEventListener('DOMContentLoaded', function () {
        // Leaflet est chargé directement dans la page, pas d'iframe
        map = L.map('map', { zoomControl: true }).setView(
            [window.mapCenterLat || 6.1319, window.mapCenterLng || 1.2228],
            13
        );

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(map);

        markersLayer    = L.layerGroup().addTo(map);
        othersLayer     = L.layerGroup().addTo(map);
        itineraryLayer  = L.layerGroup().addTo(map);
        navigationLayer = L.layerGroup().addTo(map);

        addExistingMarkers();

        // ==================== CLIC SUR LA CARTE ====================
        map.on('click', function (e) {
            console.log('[GP] Clic carte, mode =', currentMode);

            if (currentMode === 'add') {
                // Supprimer l'ancien marqueur temporaire
                if (addTempMarker) {
                    map.removeLayer(addTempMarker);
                    addTempMarker = null;
                }
                // Placer le nouveau marqueur
                addTempMarker = L.marker(e.latlng, {
                    icon: createDivIcon('gp-marker-temp', '<i class="fas fa-crosshairs"></i>')
                }).addTo(map);

                document.getElementById('addLatitude').value  = e.latlng.lat.toFixed(6);
                document.getElementById('addLongitude').value = e.latlng.lng.toFixed(6);
                document.getElementById('addPatrimoineModal').classList.remove('hidden');
            }

            if (currentMode === 'navigation') {
                // Définir le point de départ
                if (navStartMarker) map.removeLayer(navStartMarker);
                navStartLatLng = e.latlng;
                navStartMarker = L.marker(e.latlng, {
                    icon: createDivIcon('gp-marker-start', '<i class="fas fa-street-view"></i>')
                }).addTo(map).bindPopup('📍 Point de départ').openPopup();

                document.getElementById('startPointInfo').innerHTML =
                    `<i class="fas fa-check-circle" style="color:#10b981"></i>
                     Départ : ${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
            }
        });

        console.log('[GP] Carte Leaflet initialisée.');
    });

    // ==================== ICÔNES DIV PERSONNALISÉES ====================
    function createDivIcon(className, html, size) {
        return L.divIcon({
            className: className,
            html: `<div>${html}</div>`,
            iconSize: size || [32, 32],
            iconAnchor: size ? [size[0] / 2, size[1] / 2] : [16, 16]
        });
    }

    // ==================== AJOUT MARQUEURS EXISTANTS ====================
    function addExistingMarkers() {
        markersLayer.clearLayers();
        othersLayer.clearLayers();

        const myData     = window.patrimoinesData      || [];
        const othersData = window.othersPatrimoinesData || [];

        // Mes patrimoines (bleu)
        myData.forEach(p => {
            const marker = L.marker([p.lat, p.lng], {
                icon: createDivIcon('gp-marker-own', '<i class="fas fa-home"></i>')
            });
            marker.bindPopup(createPopupContent(p, true), { maxWidth: 280 });
            marker.on('click', () => window.appHandlers.selectPatrimoine(p.id));
            markersLayer.addLayer(marker);
        });

        // Autres utilisateurs (orange) — seulement si visible
        if (othersVisible) {
            othersData.forEach(p => {
                const marker = L.marker([p.lat, p.lng], {
                    icon: createDivIcon('gp-marker-other', '<i class="fas fa-map-marker-alt"></i>')
                });
                marker.bindPopup(createPopupContent(p, false), { maxWidth: 280 });
                othersLayer.addLayer(marker);
            });
        }
    }

    // ==================== POPUP ====================
    function createPopupContent(p, isOwn) {
        const photoHtml = p.photo_url
            ? `<div class="gp-popup-photo"><img src="${p.photo_url}" alt="${p.nom}" style="width:100%;max-height:80px;object-fit:cover;border-radius:6px;"></div>`
            : '<div class="gp-popup-photo-empty"><i class="fas fa-image"></i> Pas de photo</div>';

        const ownerHtml = (!isOwn && p.owner_username)
            ? `<div class="gp-popup-owner"><i class="fas fa-user"></i> ${p.owner_username}</div>`
            : '';

        const actionsHtml = isOwn ? `
            <div class="gp-popup-actions">
                <button class="gp-btn gp-btn--edit"
                    onclick="window.appHandlers.editPatrimoine(${p.id}, '${p.nom.replace(/'/g, "\\'")}', ${p.lat}, ${p.lng}, event)">
                    <i class="fas fa-pen"></i> Modifier
                </button>
                <button class="gp-btn gp-btn--delete"
                    onclick="window.appHandlers.deletePatrimoine(${p.id}, event)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        ` : '';

        return `
            <div class="gp-popup">
                ${photoHtml}
                <div class="gp-popup-body">
                    ${ownerHtml}
                    <div class="gp-popup-title">${p.nom}</div>
                    <div class="gp-popup-desc">${p.description || 'Aucune description'}</div>
                    <div class="gp-popup-coords">
                        <i class="fas fa-location-dot"></i>
                        ${p.lat.toFixed(5)}, ${p.lng.toFixed(5)}
                    </div>
                    ${actionsHtml}
                </div>
            </div>
        `;
    }

    // ==================== UTILITAIRES ====================
    function setMode(mode) {
        currentMode = mode;
    }

    function showActionBar(mode) {
        document.getElementById('actionBar').classList.remove('hidden');
        ['addFormContent', 'itineraryFormContent', 'navigationFormContent'].forEach(id =>
            document.getElementById(id).classList.add('hidden')
        );
        const map2id = { add: 'addFormContent', itinerary: 'itineraryFormContent', navigation: 'navigationFormContent' };
        if (map2id[mode]) document.getElementById(map2id[mode]).classList.remove('hidden');
    }

    function hideActionBar() {
        document.getElementById('actionBar').classList.add('hidden');
    }

    function showModeIndicator(text) {
        document.getElementById('modeText').textContent = text;
        document.getElementById('modeIndicator').classList.remove('hidden');
    }

    function hideModeIndicator() {
        document.getElementById('modeIndicator').classList.add('hidden');
    }

    function formatDistance(meters) {
        return meters >= 1000
            ? (meters / 1000).toFixed(1) + ' km'
            : Math.round(meters) + ' m';
    }

    function formatDuration(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        return h > 0 ? `${h}h ${m}min` : `${m} min`;
    }

    function getCsrf() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    function previewPhoto(input, previewId) {
        const preview = document.getElementById(previewId);
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            reader.onload = e => {
                preview.innerHTML = `<img src="${e.target.result}" alt="Aperçu">`;
                preview.classList.remove('hidden');
            };
            reader.readAsDataURL(input.files[0]);
        } else {
            preview.classList.add('hidden');
        }
    }

    // ==================== HANDLERS PUBLICS ====================
    window.appHandlers = {

        // ── MODES ──────────────────────────────────────────────────────────

        handleAddMode: function () {
            setMode('add');
            showActionBar('add');
            showModeIndicator('Mode ajout — Cliquez sur la carte');
            if (addTempMarker) { map.removeLayer(addTempMarker); addTempMarker = null; }
        },

        handleItineraryMode: function () {
            setMode('itinerary');
            showActionBar('itinerary');
            showModeIndicator('Mode itinéraire — Sélectionnez les points');
            window.appHandlers.openItineraryPanel();
        },

        handleNavigationMode: function () {
            setMode('navigation');
            showActionBar('navigation');
            showModeIndicator('Mode navigation — Cliquez sur la carte pour définir le départ');
            window.appHandlers.openNavigationPanel();
        },

        cancelAction: function () {
            setMode(null);
            hideActionBar();
            hideModeIndicator();
            if (addTempMarker) { map.removeLayer(addTempMarker); addTempMarker = null; }
        },

        // ── AJOUT ──────────────────────────────────────────────────────────

        saveNewPatrimoine: function () {
            const nom         = document.getElementById('addNom').value;
            const description = document.getElementById('addDescription').value;
            const lat         = document.getElementById('addLatitude').value;
            const lng         = document.getElementById('addLongitude').value;
            const photo       = document.getElementById('addPhoto').files[0];

            if (!nom || !lat || !lng) { alert('Veuillez remplir tous les champs requis'); return; }

            const formData = new FormData();
            formData.append('nom', nom);
            formData.append('description', description);
            formData.append('latitude', lat);
            formData.append('longitude', lng);
            if (photo) formData.append('photo', photo);

            fetch('/add-patrimoine/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf() },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    window.appHandlers.closeAddModal();
                    window.appHandlers.cancelAction();
                    window.location.reload();
                } else { alert('Erreur: ' + data.message); }
            })
            .catch(() => alert("Erreur lors de l'ajout"));
        },

        // ── ÉDITION ───────────────────────────────────────────────────────

        editPatrimoine: function (id, nom, lat, lng, event) {
            if (event) event.stopPropagation();
            document.getElementById('editId').value          = id;
            document.getElementById('editNom').value         = nom;
            document.getElementById('editDescription').value = '';
            document.getElementById('editLatitude').value    = lat;
            document.getElementById('editLongitude').value   = lng;
            document.getElementById('editModal').classList.remove('hidden');
        },

        saveEdit: function () {
            const id          = document.getElementById('editId').value;
            const nom         = document.getElementById('editNom').value;
            const description = document.getElementById('editDescription').value;
            const lat         = document.getElementById('editLatitude').value;
            const lng         = document.getElementById('editLongitude').value;
            const photo       = document.getElementById('editPhoto').files[0];

            const formData = new FormData();
            formData.append('nom', nom);
            formData.append('description', description);
            formData.append('latitude', lat);
            formData.append('longitude', lng);
            if (photo) formData.append('photo', photo);

            fetch(`/edit-patrimoine/${id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf() },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    window.appHandlers.closeEditModal();
                    window.location.reload();
                } else { alert('Erreur: ' + data.message); }
            })
            .catch(() => alert('Erreur lors de la modification'));
        },

        // ── SUPPRESSION ───────────────────────────────────────────────────

        deletePatrimoine: function (id, event) {
            if (event) event.stopPropagation();
            if (!confirm('Voulez-vous vraiment supprimer ce patrimoine ?')) return;

            fetch(`/delete-patrimoine/${id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') window.location.reload();
                else alert('Erreur: ' + data.message);
            })
            .catch(() => alert('Erreur lors de la suppression'));
        },

        // ── SÉLECTION CARTE ───────────────────────────────────────────────

        selectPatrimoine: function (id) {
            document.querySelectorAll('.patrimoine-card').forEach(c => c.classList.remove('selected'));
            const card = document.getElementById(`patrimoine-${id}`);
            if (card) {
                card.classList.add('selected');
                card.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }

            const p = (window.patrimoinesData || []).find(x => x.id === id);
            if (p && map) {
                map.setView([p.lat, p.lng], 16);
                // Ouvrir le popup du marqueur correspondant
                markersLayer.eachLayer(layer => {
                    const ll = layer.getLatLng();
                    if (Math.abs(ll.lat - p.lat) < 0.00001 && Math.abs(ll.lng - p.lng) < 0.00001) {
                        layer.openPopup();
                    }
                });
            }
        },

        // ── TOGGLE AUTRES ─────────────────────────────────────────────────

        toggleOthersPatrimoines: function () {
            othersVisible = !othersVisible;
            const btn = document.getElementById('toggleOthersBtn');
            if (othersVisible) {
                btn.innerHTML = '<i class="fas fa-eye-slash"></i><span>Masquer autres</span>';
                btn.classList.remove('toggled');
                addExistingMarkers();
            } else {
                btn.innerHTML = '<i class="fas fa-eye"></i><span>Afficher autres</span>';
                btn.classList.add('toggled');
                othersLayer.clearLayers();
            }
        },

        // ── ITINÉRAIRE MULTI-POINTS ───────────────────────────────────────

        openItineraryPanel: function () {
            document.getElementById('itineraryPanel').classList.remove('hidden');
            const list = document.getElementById('itineraryList');
            const myData = window.patrimoinesData || [];
            list.innerHTML = myData.map(p => `
                <div class="check-item">
                    <input type="checkbox" value="${p.id}" id="itin-${p.id}">
                    <label for="itin-${p.id}">${p.nom}</label>
                </div>
            `).join('');
        },

        drawSelectedItinerary: function () {
            const myData = window.patrimoinesData || [];
            const mode = document.getElementById('itineraryModeSelect')
                      || document.getElementById('routingMode');
            const selectedMode = mode ? mode.value : 'driving';

            // Récupérer les patrimoines cochés dans l'ordre
            const checked = [...document.querySelectorAll('#itineraryList input[type=checkbox]:checked')];
            if (checked.length < 2) {
                alert('Sélectionnez au moins 2 patrimoines pour tracer un itinéraire.');
                return;
            }

            const points = checked.map(cb => {
                const p = myData.find(x => x.id === parseInt(cb.value));
                return p ? { lat: p.lat, lng: p.lng } : null;
            }).filter(Boolean);

            itineraryLayer.clearLayers();

            fetch('/itinerary-multi/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrf(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ points, mode: selectedMode })
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    const geojson = L.geoJSON(data.geometry, {
                        style: { color: '#7c3aed', weight: 5, opacity: 0.85 }
                    }).addTo(itineraryLayer);

                    map.fitBounds(geojson.getBounds(), { padding: [40, 40] });

                    // Marqueurs des étapes
                    points.forEach((pt, i) => {
                        L.marker([pt.lat, pt.lng], {
                            icon: createDivIcon('gp-marker-step', `<span>${i + 1}</span>`)
                        }).addTo(itineraryLayer);
                    });

                    // Info distance/durée
                    document.getElementById('routeDistance').textContent = formatDistance(data.distance);
                    document.getElementById('routeDuration').textContent = formatDuration(data.duration);
                    document.getElementById('routeInfo').classList.remove('hidden');
                    document.getElementById('navInfo').classList.add('hidden');
                    document.getElementById('infoPanel').classList.remove('hidden');
                } else {
                    alert('Erreur itinéraire : ' + data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert('Erreur lors du calcul de l\'itinéraire');
            });
        },

        clearItinerary: function () {
            if (itineraryLayer) itineraryLayer.clearLayers();
            document.getElementById('infoPanel').classList.add('hidden');
        },

        // ── NAVIGATION POINT À POINT ──────────────────────────────────────

        openNavigationPanel: function () {
            document.getElementById('navigationPanel').classList.remove('hidden');
            navStartLatLng = null;
            if (navStartMarker) { map.removeLayer(navStartMarker); navStartMarker = null; }
            document.getElementById('startPointInfo').innerHTML =
                '<i class="fas fa-info-circle"></i> Cliquez sur la carte pour définir le départ';
        },

        calculateNavigation: function () {
            if (!navStartLatLng) {
                alert('Cliquez d\'abord sur la carte pour définir le point de départ.');
                return;
            }

            const destSelect = document.getElementById('navigationDestination');
            const destId = parseInt(destSelect.value);
            if (!destId) {
                alert('Choisissez une destination.');
                return;
            }

            const modeSelect = document.getElementById('navigationModeSelect');
            const navModeEl  = document.getElementById('navMode');
            const selectedMode = modeSelect ? modeSelect.value : (navModeEl ? navModeEl.value : 'driving');

            const formData = new FormData();
            formData.append('patrimoine_id', destId);
            formData.append('start_lat', navStartLatLng.lat);
            formData.append('start_lng', navStartLatLng.lng);
            formData.append('mode', selectedMode);

            navigationLayer.clearLayers();

            fetch('/itinerary-to/', {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrf() },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    const route = data.route;

                    // Tracer la route
                    const geojson = L.geoJSON(route.geometry, {
                        style: { color: '#0ea5e9', weight: 5, opacity: 0.9 }
                    }).addTo(navigationLayer);

                    map.fitBounds(geojson.getBounds(), { padding: [40, 40] });

                    // Marqueur destination
                    L.marker([route.destination.lat, route.destination.lng], {
                        icon: createDivIcon('gp-marker-dest', '<i class="fas fa-flag-checkered"></i>')
                    }).bindPopup(`🏁 <b>${route.destination.nom}</b>`).addTo(navigationLayer).openPopup();

                    // Infos
                    document.getElementById('navDistance').textContent = formatDistance(route.distance);
                    document.getElementById('navDuration').textContent = formatDuration(route.duration);
                    document.getElementById('navInfo').classList.remove('hidden');
                    document.getElementById('routeInfo').classList.add('hidden');
                    document.getElementById('infoPanel').classList.remove('hidden');
                } else {
                    alert('Erreur navigation : ' + data.message);
                }
            })
            .catch(err => {
                console.error(err);
                alert('Erreur lors du calcul de la navigation');
            });
        },

        clearNavigation: function () {
            if (navigationLayer) navigationLayer.clearLayers();
            if (navStartMarker)  { map.removeLayer(navStartMarker); navStartMarker = null; }
            navStartLatLng = null;
            document.getElementById('infoPanel').classList.add('hidden');
            document.getElementById('startPointInfo').innerHTML =
                '<i class="fas fa-info-circle"></i> Cliquez sur la carte pour définir le départ';
        },

        // ── MODALS ────────────────────────────────────────────────────────

        closeAddModal: function () {
            document.getElementById('addPatrimoineModal').classList.add('hidden');
            document.getElementById('addForm').reset();
            document.getElementById('addPhotoPreview').classList.add('hidden');
        },

        closeEditModal: function () {
            document.getElementById('editModal').classList.add('hidden');
            document.getElementById('editForm').reset();
            document.getElementById('editPhotoPreview').classList.add('hidden');
        },

        previewAddPhoto:  function (input) { previewPhoto(input, 'addPhotoPreview'); },
        previewEditPhoto: function (input) { previewPhoto(input, 'editPhotoPreview'); },

        // ── PANNEAUX ──────────────────────────────────────────────────────

        closeItineraryPanel: function () {
            document.getElementById('itineraryPanel').classList.add('hidden');
            if (currentMode === 'itinerary') window.appHandlers.cancelAction();
        },

        closeNavigationPanel: function () {
            document.getElementById('navigationPanel').classList.add('hidden');
            if (currentMode === 'navigation') window.appHandlers.cancelAction();
        },

        closeInfoPanel: function () {
            document.getElementById('infoPanel').classList.add('hidden');
        },
    };

})();


const boundsData = JSON.parse(document.getElementById("bounds-data").textContent);

if (boundsData) {
    const bounds = L.latLngBounds(
        [boundsData.min_lat, boundsData.min_lng],
        [boundsData.max_lat, boundsData.max_lng]
    );

    map.fitBounds(bounds, {
        padding: [50, 50],   // marge visuelle agréable
        maxZoom: 16          // évite zoom excessif si points proches
    });
} else {
    map.setView([centerLat, centerLng], 13);
}