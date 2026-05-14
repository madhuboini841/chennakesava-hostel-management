const express = require('express');
const router = express.Router();
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const { get, run } = require('../db');
const AuthUser = require('../models/AuthUser');
const { sendPasswordResetEmail } = require('../utils/email');
const { authenticate } = require('../middleware/authMiddleware');

require('dotenv').config();
const JWT_SECRET = process.env.JWT_SECRET || 'fallback_secret_key';

router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    if (!email || !password) return res.status(400).json({ error: 'Email and password required' });

    try {
        let authUser = await AuthUser.findOne({ email });
        let sqliteUser = null;

        if (!authUser) {
            // Fallback: Check if user exists in SQLite (for existing demo accounts) and migrate them
            sqliteUser = await get("SELECT * FROM users WHERE email = ? AND is_active = 1", [email]);
            if (!sqliteUser) return res.status(401).json({ error: 'Invalid credentials' });

            authUser = new AuthUser({
                email: sqliteUser.email,
                password_hash: sqliteUser.password_hash
            });
            await authUser.save();
        } else {
            sqliteUser = await get("SELECT * FROM users WHERE email = ? AND is_active = 1", [email]);
            if (!sqliteUser) return res.status(401).json({ error: 'Invalid credentials' });
        }

        const isMatch = await bcrypt.compare(password, authUser.password_hash);
        if (!isMatch) return res.status(401).json({ error: 'Invalid credentials' });

        const token = jwt.sign(
            { id: sqliteUser.id, role: sqliteUser.role, name: sqliteUser.name, meal_preference: sqliteUser.meal_preference },
            JWT_SECRET,
            { expiresIn: '7d' }
        );

        res.json({
            token,
            user: { id: sqliteUser.id, name: sqliteUser.name, email: sqliteUser.email, role: sqliteUser.role, meal_preference: sqliteUser.meal_preference }
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.post('/forgot-password', async (req, res) => {
    const { email } = req.body;
    if (!email) return res.status(400).json({ error: 'Email is required' });

    try {
        const authUser = await AuthUser.findOne({ email });
        if (!authUser) {
            // Don't leak that the user doesn't exist for security reasons
            return res.json({ message: 'If that email is registered, a reset link has been sent.' });
        }

        const resetToken = crypto.randomBytes(32).toString('hex');
        const hash = await bcrypt.hash(resetToken, 10);

        authUser.resetToken = hash;
        authUser.resetTokenExpiry = Date.now() + 3600000; // 1 hour
        await authUser.save();

        const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:5173';
        const resetUrl = `${frontendUrl}/reset-password/${resetToken}?email=${email}`;

        try {
            await sendPasswordResetEmail(email, resetUrl);
            res.json({ message: 'If that email is registered, a reset link has been sent.' });
        } catch (emailErr) {
            console.error('Email sending failed:', emailErr);
            res.json({ message: `Email failed to send. For testing purposes, please use this link: ${resetUrl}` });
        }
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.post('/reset-password', async (req, res) => {
    const { email, token, newPassword } = req.body;
    if (!email || !token || !newPassword) return res.status(400).json({ error: 'Missing required fields' });

    try {
        const authUser = await AuthUser.findOne({ email });
        if (!authUser || !authUser.resetToken || !authUser.resetTokenExpiry) {
            return res.status(400).json({ error: 'Invalid or expired reset token' });
        }

        if (Date.now() > authUser.resetTokenExpiry) {
            return res.status(400).json({ error: 'Reset token has expired' });
        }

        const isValidToken = await bcrypt.compare(token, authUser.resetToken);
        if (!isValidToken) {
            return res.status(400).json({ error: 'Invalid reset token' });
        }

        const newHash = await bcrypt.hash(newPassword, 10);
        authUser.password_hash = newHash;
        authUser.resetToken = null;
        authUser.resetTokenExpiry = null;
        await authUser.save();

        // Optional: Update SQLite hash as well just to keep them in sync
        await run("UPDATE users SET password_hash = ? WHERE email = ?", [newHash, email]);

        res.json({ message: 'Password reset successful' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.post('/change-password', authenticate, async (req, res) => {
    const { currentPassword, newPassword } = req.body;
    const userId = req.user.id;
    
    if (!currentPassword || !newPassword) {
        return res.status(400).json({ error: 'Missing current or new password' });
    }

    try {
        const sqliteUser = await get("SELECT * FROM users WHERE id = ?", [userId]);
        if (!sqliteUser) return res.status(404).json({ error: 'User not found' });
        
        const email = sqliteUser.email;
        const authUser = await AuthUser.findOne({ email });
        
        if (!authUser) {
             return res.status(404).json({ error: 'Auth user not found' });
        }

        const isMatch = await bcrypt.compare(currentPassword, authUser.password_hash);
        if (!isMatch) {
            return res.status(401).json({ error: 'Incorrect current password' });
        }

        const newHash = await bcrypt.hash(newPassword, 10);
        
        // Update MongoDB
        authUser.password_hash = newHash;
        await authUser.save();
        
        // Update SQLite
        await run("UPDATE users SET password_hash = ? WHERE email = ?", [newHash, email]);

        res.json({ message: 'Password changed successfully' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

module.exports = router;
