let map, marker;
let currentLat = null;
let currentLon = null;

// Initialisation de la carte
function initMap() {
    map = L.map('map').setView([-18.8792, 47.5079], 6);
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { attribution: '© ESRI' });
    satellite.addTo(map);

    L.control.layers({
        "🛰️ Satellite": satellite,
        "🗺️ Plan": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
    }).addTo(map);

    map.on('click', function(e) {
        currentLat = e.latlng.lat;
        currentLon = e.latlng.lng;
        placeMarker(currentLat, currentLon);
        fetchPotential(currentLat, currentLon);
    });
}

// Placer le marqueur
function placeMarker(lat, lon) {
    if (marker) marker.setLatLng([lat, lon]);
    else marker = L.marker([lat, lon], { icon: L.divIcon({ className: 'custom-marker', html: '📍', iconSize: [30, 30] }) }).addTo(map);
}

// Récupérer le potentiel
async function fetchPotential(lat, lon) {
    try {
        const res = await fetch(`http://localhost:3000/api/potential?lat=${lat}&lon=${lon}`);
        const data = await res.json();
        displayResults(data);
    } catch (err) {
        console.error(err);
        displayError("Impossible de contacter le serveur");
    }
}

// Afficher les résultats du potentiel
function displayResults(data) {
    let html = `
        <div class="potential-card">
            <h3>📍 ${data.ville_proche.nom} à ${data.ville_proche.distance} km</h3>
            <div class="potential-section"><h4>☀️ Potentiel Solaire</h4><p><strong>${data.potentiel.solaire.evaluation}</strong><br>Irradiation: ${data.potentiel.solaire.irradiation}</p></div>
            <div class="potential-section"><h4>🌡️ Météo</h4><p>Temp: ${data.meteo_actuelle.temperature}°C<br>Vent: ${data.meteo_actuelle.vent} km/h</p></div>
            <div class="potential-section"><h4>🏙️ Accessibilité</h4><p>Accès électricité: ${data.potentiel.accessibilite.acces_electricite}</p></div>
            <div class="potential-summary">${data.conseil}</div>
            <div class="altitude-info">Altitude: ${data.localisation.altitude}m (${data.localisation.terrain})</div>
        </div>
    `;
    document.getElementById('results').innerHTML = html;

    // Afficher la section ML
    document.getElementById('ml-section').style.display = 'block';
}

// Afficher erreur
function displayError(msg) {
    document.getElementById('results').innerHTML = `<div class="error-message">❌ ${msg}</div>`;
}

// ==================== LECTURE DES PARAMÈTRES DEPUIS LE FORMULAIRE ====================
function getQueryParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        nb_personnes: params.get('nb_personnes'),
        nb_enfants: params.get('nb_enfants'),
        profession_pere: params.get('profession_pere'),
        profession_mere: params.get('profession_mere'),
        distance_terrain_km: params.get('distance_terrain_km'),
        acces_electricite: params.get('acces_electricite')
    };
}

// ==================== LANCEMENT AUTOMATIQUE DU ML ====================
async function launchMLRecommendation(params) {
    if (!params.nb_personnes) return;

    const payload = {
        nb_personnes: params.nb_personnes,
        nb_enfants: params.nb_enfants || 0,
        profession_pere: params.profession_pere || 'autre',
        profession_mere: params.profession_mere || 'autre',
        acces_electricite_actuel: params.acces_electricite || 'jir_coupures',
        distance_terrain_km: params.distance_terrain_km || 50,
        lat: currentLat || -18.8792,
        lon: currentLon || 47.5079
    };

    try {
        const res = await fetch('http://localhost:3000/api/recommendation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const reco = await res.json();

        const html = `
            <h4>🌟 Recommandation personnalisée</h4>
            <p><strong>Consommation estimée :</strong> ${reco.consommation_kwh_predite} kWh/mois</p>
            <p><strong>Installation solaire recommandée :</strong> ${reco.kwp_recommande} kWp</p>
            <p><strong>Production annuelle :</strong> ${reco.production_annuelle_estimee} kWh/an</p>
            <p><strong>Score de viabilité du déménagement :</strong> ${reco.score_viabilite}/100</p>
            <p style="color:#28a745; font-weight:bold;">${reco.conseil}</p>
        `;
        document.getElementById('ml-results').innerHTML = html;
    } catch (err) {
        console.error(err);
    }
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function() {
    initMap();

    // Si on arrive depuis le formulaire → on lance directement le ML
    const params = getQueryParams();
    if (params.nb_personnes) {
        // On centre la carte sur un point par défaut (on peut améliorer plus tard)
        currentLat = -18.8792;
        currentLon = 47.5079;
        placeMarker(currentLat, currentLon);
        fetchPotential(currentLat, currentLon);
        launchMLRecommendation(params);
    }
});