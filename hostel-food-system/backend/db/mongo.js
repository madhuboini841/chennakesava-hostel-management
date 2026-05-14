const mongoose = require('mongoose');

const connectMongo = async () => {
    try {
        if (!process.env.MONGO_URI) {
            console.warn("MONGO_URI not found in .env, skipping MongoDB connection.");
            return;
        }
        await mongoose.connect(process.env.MONGO_URI);
        console.log('Connected to MongoDB.');
    } catch (err) {
        console.error('Error connecting to MongoDB:', err.message);
        process.exit(1);
    }
};

module.exports = connectMongo;
