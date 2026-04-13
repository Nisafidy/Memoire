// backend/routes/potential.js
const express = require('express');
const router = express.Router();
const potentialService = require('../services/potentialService');

// GET /api/potential?lat=xxx&lon=xxx
router.get('/', async (req, res) => {
    const { lat, lon } = req.query;
    
    if (!lat || !lon) {
        return res.status(400).json({ error: "Paramètres lat et lon requis" });
    }
    
    try {
        const potential = await potentialService.getLocationPotential(
            parseFloat(lat), 
            parseFloat(lon)
        );
        res.json(potential);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;