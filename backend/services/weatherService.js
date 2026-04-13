// backend/services/weatherService.js
const axios = require('axios');

class WeatherService {
    
    async getAllData(lat, lon) {
        console.log(`🌤️ Récupération météo pour (${lat}, ${lon})`);
        
        try {
            // Appel à Open-Meteo API
            const response = await axios.get('https://api.open-meteo.com/v1/forecast', {
                params: {
                    latitude: lat,
                    longitude: lon,
                    current_weather: true,
                    timezone: 'auto'
                },
                timeout: 5000
            });

            if (response.data && response.data.current_weather) {
                const weather = response.data.current_weather;
                return {
                    success: true,
                    temperature: weather.temperature,
                    vent: weather.windspeed,
                    direction_vent: weather.winddirection,
                    condition: this.getConditionFromCode(weather.weathercode),
                    source: "Open-Meteo"
                };
            }
        } catch (error) {
            console.log("⚠️ API météo indisponible, utilisation données simulées");
        }

        // Données simulées si l'API ne répond pas
        return {
            success: true,
            temperature: 22 + Math.random() * 8,
            vent: 5 + Math.random() * 15,
            condition: ["dégagé", "nuageux", "variable"][Math.floor(Math.random() * 3)],
            source: "simulation"
        };
    }

    getConditionFromCode(code) {
        // Code 0 = dégagé, 1-3 = nuageux, 51-67 = pluie
        if (code === 0) return "dégagé";
        if (code <= 3) return "nuageux";
        if (code >= 51 && code <= 67) return "pluvieux";
        return "variable";
    }
}

module.exports = new WeatherService();