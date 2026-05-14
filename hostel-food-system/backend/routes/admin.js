const express = require('express');
const router = express.Router();
const { authenticate, isAdmin } = require('../middleware/authMiddleware');
const { query, run, get } = require('../db');
const ExcelJS = require('exceljs');
const crypto = require('crypto');
const bcrypt = require('bcrypt');
const AuthUser = require('../models/AuthUser');
const { sendRegistrationEmail } = require('../utils/email');
// 1. Get Dashboard stats for a specific date (defaults to today)
router.get('/dashboard', authenticate, isAdmin, async (req, res) => {
    let date = req.query.date || new Date().toISOString().split('T')[0];

    try {
        const totalVegRows = await get("SELECT COUNT(*) as count FROM users WHERE role='student' AND is_active=1 AND meal_preference='veg'");
        const totalNonVegRows = await get("SELECT COUNT(*) as count FROM users WHERE role='student' AND is_active=1 AND meal_preference='non-veg'");
        
        const totalVeg = totalVegRows.count;
        const totalNonVeg = totalNonVegRows.count;
        const totalStudents = totalVeg + totalNonVeg;

        const optouts = await query(`
            SELECT f.*, u.meal_preference, u.name 
            FROM food_optouts f 
            JOIN users u ON f.student_id = u.id 
            WHERE f.date = ?
        `, [date]);

        let optB = 0, optL = 0, optD = 0;
        let optBVeg = 0, optBNon = 0, optLVeg = 0, optLNon = 0, optDVeg = 0, optDNon = 0;

        optouts.forEach(o => {
            if (o.breakfast) {
                optB++;
                o.meal_preference === 'veg' ? optBVeg++ : optBNon++;
            }
            if (o.lunch) {
                optL++;
                o.meal_preference === 'veg' ? optLVeg++ : optLNon++;
            }
            if (o.dinner) {
                optD++;
                o.meal_preference === 'veg' ? optDVeg++ : optDNon++;
            }
        });

        res.json({
            date,
            totalStudents,
            totalVeg,
            totalNonVeg,
            expectedCounts: {
                breakfast: { total: totalStudents - optB, veg: totalVeg - optBVeg, nonVeg: totalNonVeg - optBNon },
                lunch: { total: totalStudents - optL, veg: totalVeg - optLVeg, nonVeg: totalNonVeg - optLNon },
                dinner: { total: totalStudents - optD, veg: totalVeg - optDVeg, nonVeg: totalNonVeg - optDNon },
            },
            optOutLists: optouts
        });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Manage Daily Menu
router.get('/menu', authenticate, isAdmin, async (req, res) => {
    try {
        const menus = await query("SELECT * FROM daily_menus ORDER BY date DESC");
        res.json(menus);
    } catch (err) {
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.post('/menu', authenticate, isAdmin, async (req, res) => {
    const { date, meal_slot, meal_type, items } = req.body;
    if (!date || !meal_slot || !meal_type || !items) {
        return res.status(400).json({ error: 'All fields required' });
    }

    try {
        const existing = await get("SELECT is_locked FROM daily_menus WHERE date = ? AND meal_slot = ? AND meal_type = ?", [date, meal_slot, meal_type]);
        
        if (existing && existing.is_locked) {
            return res.status(403).json({ error: 'Menu is locked and cannot be edited.' });
        }

        if (existing) {
            await run(
                "UPDATE daily_menus SET items = ?, updated_at = CURRENT_TIMESTAMP WHERE date = ? AND meal_slot = ? AND meal_type = ?",
                [items, date, meal_slot, meal_type]
            );
        } else {
            await run(
                "INSERT INTO daily_menus (date, meal_slot, meal_type, items) VALUES (?, ?, ?, ?)",
                [date, meal_slot, meal_type, items]
            );
            
            await run(
                "INSERT INTO notifications (user_id, message) SELECT id, ? FROM users WHERE role = 'student' AND is_active = 1",
                [`Menu updated for ${date} - ${meal_slot} (${meal_type})`]
            );
        }
        res.json({ message: 'Menu saved successfully' });
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.get('/reports/export', authenticate, isAdmin, async (req, res) => {
    const month = req.query.month || new Date().toISOString().substring(0, 7);
    
    try {
        const optouts = await query(`
            SELECT f.date, u.name, u.email, f.breakfast, f.lunch, f.dinner, f.reason 
            FROM food_optouts f 
            JOIN users u ON f.student_id = u.id 
            WHERE f.date LIKE ?
            ORDER BY f.date DESC
        `, [`${month}%`]);

        const workbook = new ExcelJS.Workbook();
        const sheet = workbook.addWorksheet(`Opt-Outs ${month}`);

        sheet.columns = [
            { header: 'Date', key: 'date', width: 15 },
            { header: 'Student Name', key: 'name', width: 25 },
            { header: 'Email', key: 'email', width: 25 },
            { header: 'Skipped Breakfast', key: 'breakfast', width: 15 },
            { header: 'Skipped Lunch', key: 'lunch', width: 15 },
            { header: 'Skipped Dinner', key: 'dinner', width: 15 },
            { header: 'Reason', key: 'reason', width: 30 }
        ];

        optouts.forEach(o => {
            sheet.addRow({
                date: o.date,
                name: o.name,
                email: o.email,
                breakfast: o.breakfast ? 'Yes' : 'No',
                lunch: o.lunch ? 'Yes' : 'No',
                dinner: o.dinner ? 'Yes' : 'No',
                reason: o.reason || 'None'
            });
        });

        res.setHeader('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
        res.setHeader('Content-Disposition', `attachment; filename=OptOutReport_${month}.xlsx`);

        await workbook.xlsx.write(res);
        res.end();
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Internal server error generating report' });
    }
});

router.post('/register-student', authenticate, isAdmin, async (req, res) => {
    const { name, email, meal_preference } = req.body;
    
    if (!name || !email) {
        return res.status(400).json({ error: 'Name and email are required' });
    }

    try {
        // Check if user already exists
        const existingSQLite = await get("SELECT id FROM users WHERE email = ?", [email]);
        if (existingSQLite) return res.status(400).json({ error: 'Email already registered' });

        // Generate temporary password
        const tempPassword = crypto.randomBytes(4).toString('hex'); // 8 characters
        const hash = await bcrypt.hash(tempPassword, 10);

        // Insert into SQLite
        await run(
            "INSERT INTO users (name, email, password_hash, role, meal_preference) VALUES (?, ?, ?, ?, ?)",
            [name, email, hash, 'student', meal_preference || 'veg']
        );

        // Insert into MongoDB
        const authUser = new AuthUser({
            email,
            password_hash: hash
        });
        await authUser.save();

        // Send Email
        try {
            await sendRegistrationEmail(email, tempPassword);
            res.json({ message: 'Student registered successfully. Temporary password sent to their email.' });
        } catch (emailErr) {
            console.error('Email sending failed, but user was created:', emailErr);
            res.json({ message: `Student registered successfully, but email failed to send. Please give them this temporary password manually: ${tempPassword}` });
        }
    } catch (error) {
        console.error('Registration Error:', error);
        res.status(500).json({ error: 'Failed to register student' });
    }
});

module.exports = router;
