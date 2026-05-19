const Database = require('better-sqlite3');
const path = require('path');
const bcrypt = require('bcrypt');

const dbPath = path.resolve(__dirname, 'database.sqlite');
const db = new Database(dbPath);

console.log('Connected to SQLite database via better-sqlite3.');

// Users Table
db.exec(`
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
db.exec(`
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
db.exec(`
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
db.exec(`
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_read BOOLEAN DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
`);

async function initDefaults() {
    const admin = db.prepare("SELECT * FROM users WHERE email = 'admin@hostel.com'").get();
    if (!admin) {
        const hash = await bcrypt.hash('admin123', 10);
        db.prepare("INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)").run('Admin', 'admin@hostel.com', hash, 'admin');
        console.log('Default admin created: admin@hostel.com / admin123');
    }

    const student = db.prepare("SELECT * FROM users WHERE email = 'student@hostel.com'").get();
    if (!student) {
        const hash = await bcrypt.hash('student123', 10);
        db.prepare("INSERT INTO users (name, email, password_hash, role, meal_preference) VALUES (?, ?, ?, ?, ?)").run('Test Student', 'student@hostel.com', hash, 'student', 'veg');
        console.log('Default student created: student@hostel.com / student123');
    }
}
initDefaults();

// Wrapper functions returning Promises to keep backwards compatibility with the rest of the app
function query(sql, params = []) {
    return new Promise((resolve, reject) => {
        try {
            const rows = db.prepare(sql).all(...params);
            resolve(rows);
        } catch (err) {
            reject(err);
        }
    });
}

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        try {
            const info = db.prepare(sql).run(...params);
            // Provide the same object structure that sqlite3 provides in its callback 'this'
            resolve({ lastID: info.lastInsertRowid, changes: info.changes });
        } catch (err) {
            reject(err);
        }
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        try {
            const row = db.prepare(sql).get(...params);
            resolve(row); // returns undefined if not found, matching sqlite3
        } catch (err) {
            reject(err);
        }
    });
}

module.exports = { db, query, run, get };
