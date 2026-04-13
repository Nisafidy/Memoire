// backend/test-apis-complet.js (version corrigée)
const axios = require('axios');

// Couleurs pour la console
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m'
};

// Villes à tester
const villes = [
    { nom: 'Antananarivo', lat: -18.8792, lon: 47.5079 },
    { nom: 'Toamasina', lat: -18.1667, lon: 49.3833 },
    { nom: 'Mahajanga', lat: -15.7167, lon: 46.3167 },
    { nom: 'Fianarantsoa', lat: -21.4333, lon: 47.0833 },
    { nom: 'Toliara', lat: -23.3500, lon: 43.6667 }
];

// 1. TEST PVGIS
async function testPVGIS(ville) {
    console.log(`${colors.blue}📡 Test PVGIS pour ${ville.nom}...${colors.reset}`);
    
    try {
        const response = await axios.get('https://re.jrc.ec.europa.eu/api/v5_2/PVcalc', {
            params: {
                lat: ville.lat,
                lon: ville.lon,
                peakpower: 1,
                loss: 14,
                outputformat: 'json'
            },
            timeout: 10000
        });

        if (response.data && response.data.outputs) {
            const data = response.data.outputs;
            console.log(`${colors.green}✅ PVGIS OK pour ${ville.nom}${colors.reset}`);
            console.log(`   Production annuelle: ${data.totals.fixed.E_y.toFixed(0)} kWh/an (pour 1 kWc)`);
            console.log(`   Irradiation annuelle: ${data.totals.fixed.H_i_opt.toFixed(0)} kWh/m²/an`);
            return {
                success: true,
                production: data.totals.fixed.E_y,
                irradiation: data.totals.fixed.H_i_opt
            };
        }
    } catch (error) {
        console.log(`${colors.red}❌ PVGIS erreur pour ${ville.nom}: ${error.message}${colors.reset}`);
        return { success: false };
    }
}

// 2. TEST Open-Meteo (prévisions)
async function testOpenMeteoForecast(ville) {
    console.log(`${colors.blue}📡 Test Open-Meteo (prévisions) pour ${ville.nom}...${colors.reset}`);
    
    try {
        const response = await axios.get('https://api.open-meteo.com/v1/forecast', {
            params: {
                latitude: ville.lat,
                longitude: ville.lon,
                current_weather: true,
                daily: 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                timezone: 'auto',
                forecast_days: 3
            },
            timeout: 10000
        });

        if (response.data && response.data.current_weather) {
            console.log(`${colors.green}✅ Open-Meteo OK pour ${ville.nom}${colors.reset}`);
            console.log(`   Météo actuelle: ${response.data.current_weather.temperature}°C, vent: ${response.data.current_weather.windspeed} km/h`);
            return { success: true, data: response.data };
        }
    } catch (error) {
        console.log(`${colors.red}❌ Open-Meteo erreur pour ${ville.nom}: ${error.message}${colors.reset}`);
        return { success: false };
    }
}

// 3. TEST Open-Meteo (historique)
async function testOpenMeteoHistorical(ville) {
    console.log(`${colors.blue}📡 Test Open-Meteo (historique) pour ${ville.nom}...${colors.reset}`);
    
    const today = new Date();
    const lastYear = new Date();
    lastYear.setFullYear(today.getFullYear() - 1);
    
    const endDate = today.toISOString().split('T')[0];
    const startDate = lastYear.toISOString().split('T')[0];
    
    try {
        const response = await axios.get('https://archive-api.open-meteo.com/v1/archive', {
            params: {
                latitude: ville.lat,
                longitude: ville.lon,
                start_date: startDate,
                end_date: endDate,
                daily: 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                timezone: 'auto'
            },
            timeout: 15000
        });

        if (response.data && response.data.daily) {
            console.log(`${colors.green}✅ Open-Meteo historique OK pour ${ville.nom}${colors.reset}`);
            console.log(`   Données disponibles: ${response.data.daily.time.length} jours`);
            return { success: true, data: response.data };
        }
    } catch (error) {
        console.log(`${colors.red}❌ Open-Meteo historique erreur pour ${ville.nom}: ${error.message}${colors.reset}`);
        return { success: false };
    }
}

// 4. TEST NASA POWER
async function testNASAPOWER(ville) {
    console.log(`${colors.blue}📡 Test NASA POWER pour ${ville.nom}...${colors.reset}`);
    
    try {
        const response = await axios.get('https://power.larc.nasa.gov/api/temporal/daily/point', {
            params: {
                parameters: 'ALLSKY_SFC_SW_DWN,T2M,PRECTOTCORR',
                community: 'RE',
                longitude: ville.lon,
                latitude: ville.lat,
                start: 2023,
                end: 2023,
                format: 'JSON'
            },
            timeout: 15000
        });

        if (response.data && response.data.properties) {
            console.log(`${colors.green}✅ NASA POWER OK pour ${ville.nom}${colors.reset}`);
            console.log(`   Données disponibles: OK`);
            return { success: true, data: response.data };
        }
    } catch (error) {
        console.log(`${colors.red}❌ NASA POWER erreur pour ${ville.nom}: ${error.message}${colors.reset}`);
        return { success: false };
    }
}

// Fonction principale pour tester toutes les villes
async function testAll() {
    console.log(`${colors.yellow}========================================${colors.reset}`);
    console.log(`${colors.yellow}🔍 TEST COMPLET DES APIS POUR MADAGASCAR${colors.reset}`);
    console.log(`${colors.yellow}========================================${colors.reset}\n`);
    
    const results = [];
    
    for (const ville of villes) {
        console.log(`\n${colors.yellow}📍 VILLE: ${ville.nom} (${ville.lat}, ${ville.lon})${colors.reset}`);
        console.log('----------------------------------------');
        
        const villeResult = {
            nom: ville.nom,
            pvgis: await testPVGIS(ville),
            openMeteoForecast: await testOpenMeteoForecast(ville),
            openMeteoHistorical: await testOpenMeteoHistorical(ville),
            nasaPower: await testNASAPOWER(ville)
        };
        
        results.push(villeResult);
        
        // Pause pour éviter de surcharger les APIs
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Afficher le résumé
    console.log(`\n${colors.yellow}========================================${colors.reset}`);
    console.log(`${colors.yellow}📊 RÉSUMÉ DES TESTS${colors.reset}`);
    console.log(`${colors.yellow}========================================${colors.reset}\n`);
    
    for (const result of results) {
        console.log(`\n${result.nom}:`);
        console.log(`  PVGIS: ${result.pvgis.success ? '✅' : '❌'}`);
        console.log(`  Open-Meteo (prévisions): ${result.openMeteoForecast.success ? '✅' : '❌'}`);
        console.log(`  Open-Meteo (historique): ${result.openMeteoHistorical.success ? '✅' : '❌'}`);
        console.log(`  NASA POWER: ${result.nasaPower.success ? '✅' : '❌'}`);
    }
    
    console.log(`\n${colors.green}✅ Tests terminés!${colors.reset}`);
}

// Lancer les tests
testAll().catch(error => {
    console.error('Erreur fatale:', error);
});