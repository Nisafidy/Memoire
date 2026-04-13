const weatherService = require('./weatherService');
const axios = require('axios');

class PotentialService {
    
    constructor() {
        this.villes = [
            { nom: "Antananarivo", lat: -18.8792, lon: 47.5079 },
            { nom: "Toamasina", lat: -18.1667, lon: 49.3833 },
            { nom: "Mahajanga", lat: -15.7167, lon: 46.3167 },
            { nom: "Fianarantsoa", lat: -21.4333, lon: 47.0833 },
            { nom: "Toliara", lat: -23.3500, lon: 43.6667 },
            { nom: "Antsiranana", lat: -12.2667, lon: 49.2833 }
        ];
    }

    calculerDistance(lat1, lon1, lat2, lon2) {
        const R = 6371;
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
        return Math.round(R * c);
    }

    trouverVilleProche(lat, lon) {
        let plusProche = null;
        let distanceMin = Infinity;

        for (const ville of this.villes) {
            const distance = this.calculerDistance(lat, lon, ville.lat, ville.lon);
            if (distance < distanceMin) {
                distanceMin = distance;
                plusProche = { ...ville, distance: distance };
            }
        }
        return plusProche;
    }

    async evaluerPotentielSolaire(lat, lon, altitude) {
        console.log(`📡 Appel PVGIS pour (${lat}, ${lon})`);

        try {
            const response = await axios.get('https://re.jrc.ec.europa.eu/api/v5_2/PVcalc', {
                params: {
                    lat: lat,
                    lon: lon,
                    peakpower: 1,
                    loss: 14,
                    outputformat: 'json'
                },
                timeout: 12000
            });

            if (response.data && response.data.outputs && response.data.outputs.totals) {
                const totals = response.data.outputs.totals.fixed || response.data.outputs.totals;
                const productionAnnuelle = totals.E_y || 1500;
                const irradiation = totals.H_i_opt || 1800;

                let texte = "Modéré";
                if (productionAnnuelle > 1650) texte = "Excellent";
                else if (productionAnnuelle > 1450) texte = "Très bon";
                else if (productionAnnuelle > 1250) texte = "Bon";

                return {
                    irradiation: Math.round(irradiation),
                    production: Math.round(productionAnnuelle),
                    texte: texte,
                    source: "PVGIS"
                };
            }
        } catch (error) {
            console.log(`⚠️ PVGIS indisponible: ${error.message}`);
        }

        // Fallback selon altitude
        console.log("Utilisation fallback selon altitude");
        if (altitude > 1500) return { irradiation: 1900, production: 1650, texte: "Excellent", source: "estimation" };
        if (altitude > 800) return { irradiation: 1750, production: 1550, texte: "Très bon", source: "estimation" };
        if (altitude > 200) return { irradiation: 1650, production: 1450, texte: "Bon", source: "estimation" };
        return { irradiation: 1600, production: 1400, texte: "Modéré", source: "estimation" };
    }

    estimerAccesElectricite(distance, typeTerrain) {
        let acces = 70;
        if (distance > 200) acces -= 30;
        else if (distance > 100) acces -= 15;
        else if (distance > 50) acces -= 5;

        if (typeTerrain.includes("haute montagne")) acces -= 25;
        else if (typeTerrain.includes("montagne")) acces -= 15;
        else if (typeTerrain.includes("colline")) acces -= 5;

        return Math.max(10, Math.min(95, Math.round(acces)));
    }

    getTypeTerrain(altitude) {
        if (altitude < 200) return "plaine/côtière";
        if (altitude < 800) return "colline";
        if (altitude < 1500) return "montagne";
        return "haute montagne";
    }

    genererConseil(potentielTexte, accesElectricite, typeTerrain) {
        if (potentielTexte === "Excellent" && accesElectricite > 70) return "✅ Zone idéale pour l'installation solaire autonome";
        if (potentielTexte === "Très bon" && accesElectricite > 50) return "👍 Bon potentiel, installation solaire fortement recommandée";
        if (accesElectricite < 30) return "⚠️ Zone très isolée : privilégier une installation autonome avec batteries";
        if (typeTerrain.includes("montagne")) return "🏔️ Terrain montagneux : étude technique recommandée avant installation";
        return "📊 Potentiel correct. Une simulation personnalisée avec votre profil familial est conseillée.";
    }

    async getLocationPotential(lat, lon) {
        console.log(`🔍 Analyse potentiel pour (${lat}, ${lon})`);

        let altitude = 0;
        try {
            const elevResponse = await axios.get('https://api.open-meteo.com/v1/elevation', {
                params: { latitude: lat, longitude: lon }
            });
            altitude = elevResponse.data.elevation?.[0] || elevResponse.data.elevation || 0;
        } catch (error) {
            console.log("⚠️ Altitude non disponible, utilisation 0");
        }

        const meteo = await weatherService.getAllData(lat, lon);
        const villeProche = this.trouverVilleProche(lat, lon);
        const typeTerrain = this.getTypeTerrain(altitude);
        const potentielSolaire = await this.evaluerPotentielSolaire(lat, lon, altitude);
        const accesElectricite = this.estimerAccesElectricite(villeProche.distance, typeTerrain);
        const conseil = this.genererConseil(potentielSolaire.texte, accesElectricite, typeTerrain);

        return {
            localisation: {
                latitude: parseFloat(lat.toFixed(6)),
                longitude: parseFloat(lon.toFixed(6)),
                altitude: Math.round(altitude),
                terrain: typeTerrain
            },
            ville_proche: villeProche,
            meteo_actuelle: {
                temperature: meteo.temperature || "N/A",
                condition: meteo.condition || "N/A",
                vent: meteo.vent || "N/A"
            },
            potentiel: {
                solaire: {
                    evaluation: potentielSolaire.texte,
                    irradiation: potentielSolaire.irradiation + " kWh/m²/an",
                    production_annuelle: potentielSolaire.production + " kWh/kWc/an",
                    source: potentielSolaire.source
                },
                accessibilite: {
                    acces_electricite: accesElectricite + "%",
                    distance_ville: villeProche.distance + " km"
                }
            },
            conseil: conseil
        };
    }
}

module.exports = new PotentialService();