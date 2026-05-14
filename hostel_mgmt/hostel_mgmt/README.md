# 🏠 HostelPro — Hostel Management System

A complete, beginner-friendly Hostel Management Web App built with:
- **Backend**: Python Flask
- **Database**: MySQL
- **Auth**: bcrypt password hashing
- **Frontend**: Pure HTML/CSS/JavaScript (no frameworks)

---

## 📁 Folder Structure

```
hostel_mgmt/
│
├── app.py                    ← Main Flask backend (all routes & logic)
├── requirements.txt          ← Python dependencies
├── database.sql              ← MySQL schema + seed data
├── README.md                 ← This file
│
├── templates/                ← HTML pages (Jinja2 templates)
│   ├── login.html            ← Login page (student + admin)
│   ├── student_dashboard.html← Student portal
│   ├── admin_dashboard.html  ← Admin panel
│   └── register.html         ← Add new student (admin only)
│
└── static/
    └── css/
        └── style.css         ← All CSS styles
```

---

## ⚙️ Prerequisites

Make sure these are installed on your system:

1. **Python 3.8+**  → https://www.python.org/downloads/
2. **MySQL 8.0+**   → https://dev.mysql.com/downloads/
3. **pip** (comes with Python)

---

## 🚀 Step-by-Step Setup

### Step 1: Download / Clone the Project

```bash
# If you downloaded the zip, extract it and navigate to the folder:
cd hostel_mgmt
```

### Step 2: Create a Python Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask
- mysql-connector-python
- bcrypt
- Flask-Session

### Step 4: Set Up the MySQL Database

Open MySQL in your terminal:

```bash
mysql -u root -p
```

Then run the SQL file:

```sql
SOURCE /full/path/to/hostel_mgmt/database.sql;
-- OR copy-paste the contents of database.sql and run it
```

Or from the terminal directly:

```bash
mysql -u root -p < database.sql
```

### Step 5: Configure Database Connection in app.py

Open `app.py` and find the `DB_CONFIG` section (around line 20):

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',        # ← Change to your MySQL username
    'password': '',        # ← Change to your MySQL password
    'database': 'hostel_db',
    'autocommit': True
}
```

Update `user` and `password` to match your MySQL credentials.

### Step 6: Run the App

```bash
python app.py
```

You should see:
```
[INFO] Default admin created: admin@hostel.com / admin123
 * Running on http://127.0.0.1:5000
```

### Step 7: Open in Browser

Visit: **http://localhost:5000**

---

## 🔑 Default Login Credentials

| Role    | Email               | Password   |
|---------|---------------------|------------|
| Admin   | admin@hostel.com    | admin123   |
| Student | (create via admin)  | (you set)  |

---

## 📋 Features Summary

### Admin Can:
- ✅ Login securely
- ✅ View dashboard with summary stats
- ✅ Register new students
- ✅ View all students
- ✅ Assign/change room for any student
- ✅ Remove students (soft delete)
- ✅ Add new rooms
- ✅ View all rooms with occupancy bar
- ✅ Manage fee status (mark paid/pending/overdue)
- ✅ View all complaints with student details
- ✅ Update complaint status + respond
- ✅ Post notices with priority levels

### Student Can:
- ✅ Login securely
- ✅ View personal info (name, roll no, course, room)
- ✅ View room details (floor, type, monthly fee)
- ✅ View fee payment history
- ✅ Submit complaints with category
- ✅ Track complaint status + see admin response
- ✅ View all notice board announcements

---

## 🛠️ API Routes Reference

| Method | Route                              | Description                    |
|--------|------------------------------------|--------------------------------|
| GET    | /                                  | Redirect based on login state  |
| GET/POST | /login                           | Login page                     |
| GET    | /logout                            | Clear session & logout         |
| GET/POST | /register                        | Register student (admin only)  |
| GET    | /student/dashboard                 | Student portal                 |
| POST   | /complaints/submit                 | Submit complaint (student)     |
| GET    | /admin/dashboard                   | Admin panel                    |
| POST   | /notices/add                       | Post notice (admin)            |
| POST   | /complaints/update/<id>            | Update complaint (admin)       |
| POST   | /fees/update/<id>                  | Update fee status (admin)      |
| POST   | /students/assign-room/<id>         | Assign room (admin)            |
| POST   | /students/delete/<id>              | Remove student (admin)         |
| POST   | /rooms/add                         | Add room (admin)               |
| GET    | /api/students                      | JSON list of students          |
| GET    | /api/rooms                         | JSON list of rooms             |

---

## ❗ Troubleshooting

**"Can't connect to MySQL"**
→ Make sure MySQL is running: `sudo service mysql start` (Linux) or start from MySQL Workbench

**"Module not found"**
→ Make sure your virtual environment is activated and you ran `pip install -r requirements.txt`

**"Access denied for user 'root'"**
→ Check your MySQL username/password in `DB_CONFIG` in `app.py`

**"Table doesn't exist"**
→ Make sure you ran `database.sql` in MySQL first

---

## 🔮 Phase 2 — Planned Features (NOT implemented)

These are advanced features for a future version:

1. 💳 **Payment Integration** — Razorpay/Stripe for online fee payment
2. 📱 **Gate Pass QR** — Generate QR codes for student entry/exit
3. 🔒 **Digital Locker** — Assign locker numbers to students
4. 🔔 **Notifications** — Email/SMS alerts for fee due, complaints
5. 🌙 **Dark Mode** — Toggle between light and dark theme
6. 📊 **Reports & Analytics** — Monthly fee collection, occupancy charts
7. 📲 **Mobile App** — React Native companion app
8. 🔐 **OTP Login** — Phone number based OTP authentication

---

## 📝 License

Free to use for educational purposes.
