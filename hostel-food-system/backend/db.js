const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bcrypt = require('bcrypt');

const dbPath = path.resolve(__dirname, 'database.sqlite');
const db = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error connecting to SQLite database:', err.message);
    } else {
        console.log('Connected to SQLite database.');
        initDB();
    }
});

function initDB() {
    db.serialize(() => {
        // Users Table
        db.run(`
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT CHECK( role IN ('student', 'admin') ) DEFAULT 'student',
                meal_preference TEXT CHECK( meal_preference IN ('veg', 'non-veg') ) DEFAULT 'veg',
                is_active BOOLEAN DEFAULT 1
            )
        `);

        // Daily Menu Table
        db.run(`
            CREATE TABLE IF NOT EXISTS daily_menus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                meal_slot TEXT CHECK( meal_slot IN ('breakfast', 'lunch', 'dinner') ) NOT NULL,
                meal_type TEXT CHECK( meal_type IN ('veg', 'non-veg') ) NOT NULL,
                items TEXT NOT NULL,
                is_locked BOOLEAN DEFAULT 0,
                posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, meal_slot, meal_type)
            )
        `);

        // Food Opt-outs Table
        db.run(`
            CREATE TABLE IF NOT EXISTS food_optouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                breakfast BOOLEAN DEFAULT 0,
                lunch BOOLEAN DEFAULT 0,
                dinner BOOLEAN DEFAULT 0,
                reason TEXT,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE(student_id, date)
            )
        `);

        // Notifications Table
        db.run(`
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        `);

        // Make sure a default admin exists
        db.get("SELECT * FROM users WHERE email = 'admin@hostel.com'", async (err, row) => {
            if (!row) {
                const hash = await bcrypt.hash('admin123', 10);
                db.run(
                    "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                    ['Admin', 'admin@hostel.com', hash, 'admin']
                );
                console.log('Default admin created: admin@hostel.com / admin123');
            }
        });
        
        // Also a default student for easier testing
        db.get("SELECT * FROM users WHERE email = 'student@hostel.com'", async (err, row) => {
            if (!row) {
                const hash = await bcrypt.hash('student123', 10);
                db.run(
                    "INSERT INTO users (name, email, password_hash, role, meal_preference) VALUES (?, ?, ?, ?, ?)",
                    ['Test Student', 'student@hostel.com', hash, 'student', 'veg']
                );
                console.log('Default student created: student@hostel.com / student123');
            }
        });
    });
}

function query(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
}

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve(this);
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
}

module.exports = { db, query, run, get };
