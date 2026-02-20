// dashboardScript.js - Fix iframe Folium + bon contexte L

(function() {
    // ==================== ÉTAT GLOBAL ====================
    let map = null;
    let iframeWindow = null; // contexte Leaflet (iframe ou window)
    let markersLayer = null;
    let othersLayer = null;
    let itineraryLayer = null;
    let navigationLayer = null;
    let currentMode = null;
    let addMarker = null;
    let startMarker = null;
    let destMarker = null;
    let selectedPatrimoineId = null;
    let othersVisible = true;

    // ==================== INITIALISATION ====================
    document.addEventListener('DOMContentLoaded', function() {
        tryInitMap(0);
    });

    /**
     * Folium génère la carte dans un <iframe> avec une variable "map_xxxxxxxx".
     * On cherche dans l'iframe d'abord, puis dans window en fallback.
     * On stocke iframeWindow pour utiliser le bon L (Leaflet).
     */
    function findFoliumMap() {
        // 1. Chercher dans les iframes du div#map
        const iframes = document.querySelectorAll('#map iframe');
        for (const iframe of iframes) {
            try {
                const iWin = iframe.contentWindow;
                if (!iWin) continue;

                for (const key of Object.keys(iWin)) {
                    if (key.startsWith('map_') && iWin[key] && typeof iWin[key].on === 'function') {
                        console.log('[GP] Carte trouvée dans iframe :', key);
                        iframeWindow = iWin;
                        return iWin[key];
                    }
                }

                if (iWin.map && typeof iWin.map.on === 'function') {
                    console.log('[GP] Carte trouvée dans iframe : window.map');
                    iframeWindow = iWin;
                    return iWin.map;
                }
            } catch(e) {
                console.warn('[GP] Accès iframe bloqué (cross-origin?):', e);
            }
        }

        // 2. Fallback : window principal
        for (const key of Object.keys(window)) {
            if (key.startsWith('map_') && window[key] && typeof window[key].on === 'function') {
                console.log('[GP] Carte trouvée dans window principal :', key);
                iframeWindow = window;
                return window[key];
            }
        }

        if (window.map && typeof window.map.on === 'function') {
            iframeWindow = window;
            return window.map;
        }

        return null;
    }

    // Toujours utiliser LE BON L (celui du même contexte que la carte)
    function getL() {
        return (iframeWindow && iframeWindow.L) ? iframeWindow.L : window.L;
    }

    function tryInitMap(attempt) {
        const found = findFoliumMap();
        if (found) {
            map = found;
            initLayers();
        } else if (attempt < 30) {
            setTimeout(() => tryInitMap(attempt + 1), 300);
        } else {
            console.error('[GP] Impossible de trouver la carte Folium après 30 tentatives.');
            console.log('[GP] Iframes présentes :', document.querySelectorAll('#map iframe').length);
            console.log('[GP] Clés window contenant "map" :', Object.keys(window).filter(k => k.includes('map')));
        }
    }

    function initLayers() {
        const L = getL();
        markersLayer    = L.layerGroup().addTo(map);
        othersLayer     = L.layerGroup().addTo(map);
        itineraryLayer  = L.layerGroup().addTo(map);
        navigationLayer = L.layerGroup().addTo(map);

        addExistingMarkers();
        map.on('click', onMapClick);
        console.log('[GP] Carte initialisée, clics activés.');
    }

    // ==================== MARQUEURS EXISTANTS ====================
    function addExistingMarkers() {
        const L = getL();
        markersLayer.clearLayers();

        if (window.patrimoinesData) {
            window.patrimoinesData.forEach(p => {
                const marker = L.marker([p.lat, p.lng], {
                    icon: L.divIcon({
                        className: 'gp-marker-own',
                        html: '<div><i class="fas fa-home"></i></div>',
                        iconSize: [28, 28],
                        iconAnchor: [14, 14]
                    })
                }).bindPopup(createPopupContent(p, true));

                marker.on('click', () => window.appHandlers.selectPatrimoine(p.id));
                markersLayer.addLayer(marker);
            });
        }

        if (window.othersPatrimoinesData && othersVisible) {
            othersLayer.clearLayers();
            window.othersPatrimoinesData.forEach(p => {
                const marker = L.marker([p.lat, p.lng], {
                    icon: L.divIcon({
                        className: 'gp-marker-other',
                        html: '<div><i class="fas fa-map-marker-alt"></i></div>',
                        iconSize: [28, 28],
                        iconAnchor: [14, 14]
                    })
                }).bindPopup(createPopupContent(p, false));

                othersLayer.addLayer(marker);
            });
        }
    }

    // ==================== CRÉATION POPUP ====================
    // IMPORTANT : les boutons dans les popups de l'iframe appellent window.parent.appHandlers
    function createPopupContent(p, isOwn) {
        const photoHtml = p.photo_url
            ? `<div class="gp-popup-photo"><img src="${p.photo_url}" alt="${p.nom}" style="width:100%;height:100%;object-fit:cover;max-height:72px;"></div>`
            : '<div class="gp-popup-photo-empty"><i class="fas fa-image"></i> Pas de photo</div>';

        const ownerHtml = !isOwn && p.owner_username
            ? `<div class="gp-popup-owner"><i class="fas fa-user"></i> ${p.owner_username}</div>`
            : '';

        const actionsHtml = isOwn ? `
            <div class="gp-popup-actions">
                <button class="gp-btn gp-btn--edit"
                    onclick="(window.parent||window).appHandlers.editPatrimoine(${p.id}, '${p.nom.replace(/'/g, "\\'")}', ${p.lat}, ${p.lng}, event)">
                    <i class="fas fa-pen"></i> Modifier
                </button>
                <button class="gp-btn gp-btn--delete"
                    onclick="(window.parent||window).appHandlers.deletePatrimoine(${p.id}, event)">
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

    // ==================== GESTION DES MODES ====================
    window.appHandlers = {
        handleAddMode: function() {
            setActiveMode('add');
            showActionBar('add');
            showModeIndicator('Mode ajout - Cliquez sur la carte');
            if (addMarker && map) { map.removeLayer(addMarker); addMarker = null; }
        },

        handleItineraryMode: function() {
            setActiveMode('itinerary');
            showActionBar('itinerary');
            showModeIndicator('Mode itinéraire - Sélectionnez les points');
            openItineraryPanel();
        },

        handleNavigationMode: function() {
            setActiveMode('navigation');
            showActionBar('navigation');
            showModeIndicator('Mode navigation - Choisissez départ et destination');
            openNavigationPanel();
        },

        cancelAction: function() {
            setActiveMode(null);
            hideActionBar();
            hideModeIndicator();
            if (addMarker && map) { map.removeLayer(addMarker); addMarker = null; }
        },

        // ==================== AJOUT PATRIMOINE ====================
        saveNewPatrimoine: function() {
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

            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch('/add-patrimoine/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
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
            .catch(err => { console.error(err); alert("Erreur lors de l'ajout"); });
        },

        // ==================== ÉDITION PATRIMOINE ====================
        editPatrimoine: function(id, nom, lat, lng, event) {
            if (event) event.stopPropagation();
            document.getElementById('editId').value          = id;
            document.getElementById('editNom').value         = nom;
            document.getElementById('editDescription').value = '';
            document.getElementById('editLatitude').value    = lat;
            document.getElementById('editLongitude').value   = lng;
            document.getElementById('editModal').classList.remove('hidden');
        },

        saveEdit: function() {
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

            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/edit-patrimoine/${id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    window.appHandlers.closeEditModal();
                    window.location.reload();
                } else { alert('Erreur: ' + data.message); }
            })
            .catch(err => { console.error(err); alert('Erreur lors de la modification'); });
        },

        // ==================== SUPPRESSION PATRIMOINE ====================
        deletePatrimoine: function(id, event) {
            if (event) event.stopPropagation();
            if (!confirm('Voulez-vous vraiment supprimer ce patrimoine ?')) return;

            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch(`/delete-patrimoine/${id}/`, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrftoken, 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') { window.location.reload(); }
                else { alert('Erreur: ' + data.message); }
            })
            .catch(err => { console.error(err); alert('Erreur lors de la suppression'); });
        },

        // ==================== SÉLECTION PATRIMOINE ====================
        selectPatrimoine: function(id) {
            selectedPatrimoineId = id;
            document.querySelectorAll('.patrimoine-card').forEach(c => c.classList.remove('selected'));
            const card = document.getElementById(`patrimoine-${id}`);
            if (card) card.classList.add('selected');

            if (map && window.patrimoinesData) {
                const p = window.patrimoinesData.find(p => p.id === id);
                if (p) {
                    map.setView([p.lat, p.lng], 15);
                    markersLayer.eachLayer(layer => {
                        const ll = layer.getLatLng();
                        if (ll.lat === p.lat && ll.lng === p.lng) layer.openPopup();
                    });
                }
            }
        },

        // ==================== TOGGLE AUTRES PATRIMOINES ====================
        toggleOthersPatrimoines: function() {
            othersVisible = !othersVisible;
            const btn = document.getElementById('toggleOthersBtn');
            if (othersVisible) {
                btn.innerHTML = '<i class="fas fa-eye-slash"></i><span>Masquer autres</span>';
                btn.classList.remove('toggled');
                addExistingMarkers();
            } else {
                btn.innerHTML = '<i class="fas fa-eye"></i><span>Afficher autres</span>';
                btn.classList.add('toggled');
                if (othersLayer) othersLayer.clearLayers();
            }
        },

        // ==================== MODALS ====================
        closeAddModal: function() {
            document.getElementById('addPatrimoineModal').classList.add('hidden');
            document.getElementById('addForm').reset();
            document.getElementById('addPhotoPreview').classList.add('hidden');
        },

        closeEditModal: function() {
            document.getElementById('editModal').classList.add('hidden');
            document.getElementById('editForm').reset();
            document.getElementById('editPhotoPreview').classList.add('hidden');
        },

        previewAddPhoto: function(input) { previewPhoto(input, 'addPhotoPreview'); },
        previewEditPhoto: function(input) { previewPhoto(input, 'editPhotoPreview'); },

        // ==================== PANNEAUX ====================
        closeItineraryPanel: function() {
            document.getElementById('itineraryPanel').classList.add('hidden');
            if (currentMode === 'itinerary') window.appHandlers.cancelAction();
        },

        closeNavigationPanel: function() {
            document.getElementById('navigationPanel').classList.add('hidden');
            if (currentMode === 'navigation') window.appHandlers.cancelAction();
        },

        closeInfoPanel: function() { document.getElementById('infoPanel').classList.add('hidden'); },

        drawSelectedItinerary: function() { console.log('[GP] drawSelectedItinerary — à implémenter'); },
        clearItinerary:        function() { if (itineraryLayer) itineraryLayer.clearLayers(); },
        calculateNavigation:   function() { console.log('[GP] calculateNavigation — à implémenter'); },
        clearNavigation: function() {
            if (navigationLayer) navigationLayer.clearLayers();
            if (startMarker && map) { map.removeLayer(startMarker); startMarker = null; }
            if (destMarker  && map) { map.removeLayer(destMarker);  destMarker  = null; }
        },

        logout: function() {
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            fetch('/logout/', { method: 'POST', headers: { 'X-CSRFToken': csrftoken } })
            .then(r => { window.location.href = r.redirected ? r.url : '/login/'; })
            .catch(() => { window.location.href = '/login/'; });
        }
    };

    // ==================== FONCTIONS UTILITAIRES ====================
    function setActiveMode(mode) { currentMode = mode; }

    function showActionBar(mode) {
        document.getElementById('actionBar').classList.remove('hidden');
        ['addFormContent', 'itineraryFormContent', 'navigationFormContent'].forEach(id =>
            document.getElementById(id).classList.add('hidden')
        );
        const ids = { add: 'addFormContent', itinerary: 'itineraryFormContent', navigation: 'navigationFormContent' };
        if (ids[mode]) document.getElementById(ids[mode]).classList.remove('hidden');
    }

    function hideActionBar()    { document.getElementById('actionBar').classList.add('hidden'); }

    function showModeIndicator(text) {
        document.getElementById('modeText').textContent = text;
        document.getElementById('modeIndicator').classList.remove('hidden');
    }

    function hideModeIndicator() { document.getElementById('modeIndicator').classList.add('hidden'); }

    function onMapClick(e) {
        if (currentMode === 'add') {
            const L = getL();
            if (addMarker) map.removeLayer(addMarker);
            addMarker = L.marker(e.latlng).addTo(map);
            document.getElementById('addLatitude').value  = e.latlng.lat.toFixed(6);
            document.getElementById('addLongitude').value = e.latlng.lng.toFixed(6);
            document.getElementById('addPatrimoineModal').classList.remove('hidden');
        }
    }

    function openItineraryPanel() {
        document.getElementById('itineraryPanel').classList.remove('hidden');
        const list = document.getElementById('itineraryList');
        if (window.patrimoinesData) {
            list.innerHTML = window.patrimoinesData.map(p => `
                <div class="check-item">
                    <input type="checkbox" value="${p.id}" id="itin-${p.id}">
                    <label for="itin-${p.id}">${p.nom}</label>
                </div>
            `).join('');
        }
    }

    function openNavigationPanel() {
        document.getElementById('navigationPanel').classList.remove('hidden');
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

})();