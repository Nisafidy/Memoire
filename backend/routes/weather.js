// backend/routes/weather.js
const express = require('express');
const router = express.Router();
const weatherService = require('../services/weatherService');

// GET /api/weather/data?lat=xxx&lon=xxx
router.get('/data', async (req, res) => {
    const { lat, lon } = req.query;
    
    if (!lat || !lon) {
        return res.status(400).json({ error: "Paramètres lat et lon requis" });
    }
    
    try {
        const data = await weatherService.getAllData(
            parseFloat(lat), 
            parseFloat(lon)
        );
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// GET /api/weather/test
router.get('/test', (req, res) => {
    res.json({ message: "Route météo OK" });
});

module.exports = router;