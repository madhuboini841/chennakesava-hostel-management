const express = require('express');
const router = express.Router();
const { authenticate } = require('../middleware/authMiddleware');
const { query, run, get } = require('../db');

// Helper: Check if deadline passed
function isDeadlinePassed(mealSlot) {
    const now = new Date();
    const hour = now.getHours();
    
    // Deadline: Breakfast 7 AM, Lunch/Dinner 10 AM
    if (mealSlot === 'breakfast' && hour >= 7) return true;
    if ((mealSlot === 'lunch' || mealSlot === 'dinner') && hour >= 10) return true;
    
    return false;
}

// 1. Get menus (up to 7 days ahead, and history)
router.get('/menu', authenticate, async (req, res) => {
    try {
        const menus = await query("SELECT * FROM daily_menus ORDER BY date DESC LIMIT 21");
        res.json(menus);
    } catch (err) {
        res.status(500).json({ error: 'Internal server error' });
    }
});

// 2. Get today's opt-out status for the logged-in student
router.get('/optout/today', authenticate, async (req, res) => {
    const today = new Date().toISOString().split('T')[0];
    try {
        const optout = await get("SELECT * FROM food_optouts WHERE student_id = ? AND date = ?", [req.user.id, today]);
        res.json(optout || { breakfast: 0, lunch: 0, dinner: 0 });
    } catch (err) {
        res.status(500).json({ error: 'Internal server error' });
    }
});

// 3. Submit or Edit Opt-out
router.post('/optout', authenticate, async (req, res) => {
    const { date, breakfast, lunch, dinner, reason } = req.body;
    const student_id = req.user.id;
    
    if (!date) return res.status(400).json({ error: 'Date is required' });

    const today = new Date().toISOString().split('T')[0];
    
    // If updating for today, check deadlines
    if (date === today) {
        const existing = await get("SELECT * FROM food_optouts WHERE student_id = ? AND date = ?", [student_id, date]);
        
        const oldB = existing ? existing.breakfast : 0;
        const oldL = existing ? existing.lunch : 0;
        const oldD = existing ? existing.dinner : 0;

        if (breakfast !== oldB && isDeadlinePassed('breakfast')) {
            return res.status(400).json({ error: 'Breakfast opt-out deadline (7 AM) has passed for today.' });
        }
        if ((lunch !== oldL && isDeadlinePassed('lunch')) || (dinner !== oldD && isDeadlinePassed('dinner'))) {
            return res.status(400).json({ error: 'Lunch/Dinner opt-out deadline (10 AM) has passed for today.' });
        }
    } else if (date < today) {
        return res.status(400).json({ error: 'Cannot modify past records.' });
    }

    try {
        const existing = await get("SELECT id FROM food_optouts WHERE student_id = ? AND date = ?", [student_id, date]);
        if (existing) {
            await run(
                "UPDATE food_optouts SET breakfast = ?, lunch = ?, dinner = ?, reason = ? WHERE id = ?",
                [breakfast ? 1 : 0, lunch ? 1 : 0, dinner ? 1 : 0, reason, existing.id]
            );
        } else {
            await run(
                "INSERT INTO food_optouts (student_id, date, breakfast, lunch, dinner, reason) VALUES (?, ?, ?, ?, ?, ?)",
                [student_id, date, breakfast ? 1 : 0, lunch ? 1 : 0, dinner ? 1 : 0, reason]
            );
        }
        res.json({ message: 'Opt-out updated successfully' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// 4. Get Notifications
router.get('/notifications', authenticate, async (req, res) => {
    try {
        const notifications = await query("SELECT * FROM notifications WHERE user_id = ? ORDER BY sent_at DESC LIMIT 20", [req.user.id]);
        res.json(notifications);
    } catch (err) {
        res.status(500).json({ error: 'Internal server error' });
    }
});

module.exports = router;

