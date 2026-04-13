const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

const weatherRoutes = require('./routes/weather');
const potentialRoutes = require('./routes/potential');

const app = express();
const PORT = 3000;

// ==================== CONFIGURATION ADMIN ====================
const ADMIN_EMAILS = [
    "nisafidyandrianasy@gmail.com"     // ←←← Remplace par TON VRAI EMAIL
];

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../frontend')));

// Routes existantes
app.use('/api/weather', weatherRoutes);
app.use('/api/potential', potentialRoutes);

// ====================== ROUTE QUESTIONNAIRE ======================
app.post('/api/submit-questionnaire', (req, res) => {
    const data = req.body;
    const csvPath = path.join(__dirname, '../ml/data/raw/reponses_enquete.csv');

    // Si l'email est dans la liste ADMIN → on autorise les doublons
    const isAdmin = ADMIN_EMAILS.includes(data.email);

    if (!isAdmin && fs.existsSync(csvPath)) {
        const existing = fs.readFileSync(csvPath, 'utf8');
        if (existing.includes(data.email)) {
            return res.json({ 
                success: false, 
                message: "Vous avez déjà répondu à l'enquête avec cet email. Merci !" 
            });
        }
    }

    // Création de la ligne CSV
    const header = 'email,age,statut,occupation,lieu_actuel,nb_personnes,nb_enfants,profession_pere,profession_mere,autres_actifs,projet_terrain,lieu_terrain,distance_terrain_km,consommation,acces_electricite,timestamp\n';
    const row = `"${data.email}","${data.age}","${data.statut}","${data.occupation}","${data.lieu_actuel}",${data.nb_personnes},${data.nb_enfants},"${data.profession_pere}","${data.profession_mere}","${data.autres_actifs || ''}","${data.projet_terrain}","${data.lieu_terrain || ''}",${data.distance_terrain_km},"${data.consommation}","${data.acces_electricite}",${new Date().toISOString()}\n`;

    if (!fs.existsSync(csvPath)) fs.writeFileSync(csvPath, header);
    fs.appendFileSync(csvPath, row);

    console.log(`✅ Réponse enregistrée : ${data.email} ${isAdmin ? '(ADMIN - doublons autorisés)' : ''}`);

    // Redirection vers la carte
    res.json({
        success: true,
        redirect: `/index.html?email=${encodeURIComponent(data.email)}&nb_personnes=${data.nb_personnes}&nb_enfants=${data.nb_enfants}&profession_pere=${encodeURIComponent(data.profession_pere)}&profession_mere=${encodeURIComponent(data.profession_mere)}&distance_terrain_km=${data.distance_terrain_km}&consommation=${encodeURIComponent(data.consommation)}&acces_electricite=${encodeURIComponent(data.acces_electricite)}`
    });
});

app.get('/api/test', (req, res) => res.json({ message: "✅ Serveur fonctionne !" }));

app.listen(PORT, () => {
    console.log(`✅ Serveur démarré sur http://localhost:${PORT}`);
    console.log(`   → Page d'accueil : http://localhost:3000/description.html`);
});