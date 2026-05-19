const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const studentRoutes = require('./routes/student');
const adminRoutes = require('./routes/admin');
const initCronJobs = require('./utils/cron');
require('./db'); // Initializes SQLite DB
const connectMongo = require('./db/mongo'); // MongoDB Connection

const app = express();
connectMongo(); // Initialize MongoDB
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    credentials: true
}));
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/student', studentRoutes);
app.use('/api/admin', adminRoutes);

// Health check
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', serverTime: new Date() });
});

// Start Cron Jobs
initCronJobs();

// Serve frontend static files in production
app.use(express.static(path.join(__dirname, '../frontend/dist')));

// Catch-all route to serve React app
app.get(/.*/, (req, res) => {
    res.sendFile(path.join(__dirname, '../frontend/dist/index.html'), (err) => {
        if (err) {
            res.status(500).send("Frontend build not found. Please ensure the frontend is built.");
        }
    });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log("Server running on port " + PORT);
});

