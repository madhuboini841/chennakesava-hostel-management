# ============================================================
# app.py - Hostel Management System Backend
# Flask + MySQL + bcrypt
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_file
from werkzeug.utils import secure_filename
from fpdf import FPDF
from io import BytesIO
import mysql.connector
import bcrypt
from datetime import date, datetime, timedelta
import os
import requests
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS

from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.getenv("SECRET_KEY", "hostel_secret_key_change_in_production")

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'profiles')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def log_activity(student_id, action):
    conn = get_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO student_activity_logs (student_id, action) VALUES (%s, %s)", (student_id, action))
        cursor.close()
        conn.close()

# ============================================================
# FAST2SMS REMINDER SYSTEM & SCHEDULER
# ============================================================
def get_setting(key):
    conn = get_db()
    if not conn: return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = %s", (key,))
    row = cursor.fetchone()
    cursor.close(); conn.close()
    return row['setting_value'] if row else None

def send_fast2sms(mobile_number, message, student_id=None, fee_id=None):
    api_key = get_setting('fast2sms_api_key')
    if not api_key:
        print("[SMS] Failed to send: No API Key configured.")
        return False
        
    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "q",
        "message": message,
        "language": "english",
        "flash": 0,
        "numbers": mobile_number
    }
    headers = {
        "authorization": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers)
        res_json = response.json()
        status = "sent" if res_json.get("return") else "failed"
    except Exception as e:
        status = f"error: {str(e)}"
        
    if student_id:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sms_logs (student_id, mobile_number, message, status) VALUES (%s, %s, %s, %s)",
                          (student_id, mobile_number, message, status))
            conn.commit()
            cursor.close(); conn.close()
            
    return status == "sent"

def check_and_send_due_date_reminders():
    print("[SCHEDULER] Checking fee due dates for reminders...")
    conn = get_db()
    if not conn: return
    cursor = conn.cursor(dictionary=True)
    
    today = date.today()
    cursor.execute("""
        SELECT f.id as fee_id, f.student_id, f.amount, f.due_date, 
               f.reminder_7_days_sent, f.reminder_3_days_sent, f.reminder_0_days_sent,
               s.name, s.mobile_number, s.parent_number
        FROM fees f
        JOIN students s ON f.student_id = s.id
        WHERE f.status != 'paid' AND s.status = 'active'
    """)
    pending_fees = cursor.fetchall()
    
    for fee in pending_fees:
        delta = (fee['due_date'] - today).days
        message = ""
        flag_to_update = None
        
        if delta == 7 and not fee['reminder_7_days_sent']:
            message = f"Dear {fee['name']}, friendly reminder that your hostel fee of Rs.{fee['amount']} is due in 7 days ({fee['due_date']})."
            flag_to_update = "reminder_7_days_sent"
        elif delta == 3 and not fee['reminder_3_days_sent']:
            message = f"URGENT: Dear {fee['name']}, your hostel fee of Rs.{fee['amount']} is due in 3 days ({fee['due_date']}). Please pay."
            flag_to_update = "reminder_3_days_sent"
        elif delta == 0 and not fee['reminder_0_days_sent']:
            message = f"ALERT: Dear {fee['name']}, your hostel fee of Rs.{fee['amount']} is DUE TODAY ({fee['due_date']})."
            flag_to_update = "reminder_0_days_sent"
            
        if message:
            print(f"[SMS] Sending reminder to {fee['name']}...")
            numbers = fee['mobile_number']
            if fee['parent_number']:
                numbers += f",{fee['parent_number']}"
            
            if numbers:
                success = send_fast2sms(numbers, message, student_id=fee['student_id'], fee_id=fee['fee_id'])
                if success and flag_to_update:
                    cursor.execute(f"UPDATE fees SET {flag_to_update} = TRUE WHERE id = %s", (fee['fee_id'],))
                
    conn.commit()
    cursor.close()
    conn.close()

def lock_menus(meal_slots):
    print(f"[SCHEDULER] Locking menus for {meal_slots}...")
    conn = get_db()
    if not conn: return
    cursor = conn.cursor()
    today = date.today().isoformat()
    format_strings = ','.join(['%s'] * len(meal_slots))
    cursor.execute(f"UPDATE daily_menus SET is_locked=TRUE WHERE date=%s AND meal_slot IN ({format_strings})",
                   (today, *meal_slots))
    conn.commit()
    cursor.close()
    conn.close()

def send_food_reminder():
    print("[SCHEDULER] Posting daily food opt-out reminder...")
    conn = get_db()
    if not conn: return
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins LIMIT 1")
    admin = cursor.fetchone()
    admin_id = admin[0] if admin else 1
    cursor.execute("""
        INSERT INTO notices (title, content, priority, posted_by) 
        VALUES (%s, %s, %s, %s)
    """, ("Daily Meal Opt-Out Reminder", "Don't forget to mark your meal opt-outs for today! Breakfast cutoff is 7 AM. Lunch & Dinner cutoff is 10 AM.", 'low', admin_id))
    conn.commit()
    cursor.close()
    conn.close()

def auto_backup_db():
    print("[SCHEDULER] Running daily automated database backup...")
    backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_dir, f"hostel_db_backup_{timestamp}.sql")
    
    db_user = os.getenv('DB_USER', 'root')
    db_name = os.getenv('DB_NAME', 'hostel_db')
    
    try:
        # Note: Using absolute path for mysqldump to be safe in XAMPP
        mysqldump_path = r"C:\xampp\mysql\bin\mysqldump.exe"
        if not os.path.exists(mysqldump_path):
            mysqldump_path = "mysqldump" # Fallback to system path
            
        with open(backup_file, 'w') as f:
            subprocess.run([mysqldump_path, '-u', db_user, db_name], stdout=f, check=True)
        print(f"[BACKUP] Successfully created backup at {backup_file}")
    except Exception as e:
        print(f"[BACKUP ERROR] Failed to create backup: {e}")

# Start scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_due_date_reminders, 'cron', hour=8, minute=0)
scheduler.add_job(lock_menus, 'cron', hour=7, minute=0, args=[['breakfast']])
scheduler.add_job(lock_menus, 'cron', hour=10, minute=0, args=[['lunch', 'dinner']])
scheduler.add_job(send_food_reminder, 'cron', hour=6, minute=0)
scheduler.add_job(auto_backup_db, 'cron', hour=23, minute=59)
scheduler.start()

# ============================================================
# DATABASE CONFIGURATION
# Update these values to match your MySQL setup
# ============================================================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'hostel_db'),
    'autocommit': True
}

# ============================================================
# DATABASE HELPER: Get a fresh connection
# ============================================================
def get_db():
    """Returns a MySQL connection. Call this in each route."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"[DB ERROR] {e}")
        return None

# ============================================================
# STARTUP: Create default admin if none exists
# Admin email: admin@hostel.com | Password: admin123
# ============================================================
def create_default_admin():
    conn = get_db()
    if not conn:
        print("[WARN] Could not connect to DB to create admin.")
        return
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM admins LIMIT 1")
    if not cursor.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s)",
            ("Admin", "admin@hostel.com", hashed)
        )
        print("[INFO] Default admin created: admin@hostel.com / admin123")
    cursor.close()
    conn.close()

# ============================================================
# AUTH HELPERS
# ============================================================
def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'admin'

def is_student():
    return session.get('role') == 'student'

def generate_temp_password(length=8):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(length))

def send_auth_email(to_email, subject, body_html):
    smtp_server = os.getenv('SMTP_HOST', 'smtp.office365.com')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_user = os.getenv('EMAIL_USER', 'chennakesavahostel@outlook.com')
    smtp_pass = os.getenv('EMAIL_PASS', 'ucgnftwsfdbdgizk')

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1) # Enable debug output for the terminal logs
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n[SMTP AUTH ERROR] Failed to login to {smtp_server}:{smtp_port} with {smtp_user}.")
        print(f"Details: {e.smtp_code} - {e.smtp_error.decode('utf-8') if isinstance(e.smtp_error, bytes) else e.smtp_error}\n")
        return False
    except Exception as e:
        print(f"\n[SMTP GENERAL ERROR] {e}\n")
        return False

# ============================================================
# ROUTE: Home - redirect based on login state
# ============================================================
@app.route('/')
def index():
    if is_logged_in():
        if is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

# ============================================================
# ROUTE: Login (GET = show form, POST = process login)
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'student')  # 'admin' or 'student'

        if not email or not password:
            flash("Email and password are required.", "error")
            return render_template('login.html')

        conn = get_db()
        if not conn:
            flash("Database connection error. Please try again.", "error")
            return render_template('login.html')

        cursor = conn.cursor(dictionary=True)

        if role == 'admin':
            cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        else:
            cursor.execute("SELECT * FROM students WHERE email = %s AND status = 'active'", (email,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            session['role'] = role
            
            if user.get('must_change_password'):
                session['must_change'] = True
                flash("You must change your temporary password to continue.", "info")
                return redirect(url_for('change_password'))
                
            flash(f"Welcome back, {user['name']}!", "success")
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                log_activity(user['id'], "Logged in successfully")
                return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid email or password.", "error")

    return render_template('login.html')

# ============================================================
# ROUTE: Forgot Password
# ============================================================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        role = request.form.get('role', 'student')
        
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        table = 'admins' if role == 'admin' else 'students'
        
        cursor.execute(f"SELECT id, name FROM {table} WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            cursor.execute(f"UPDATE {table} SET reset_token=%s, reset_token_expiry=%s WHERE id=%s", 
                           (token, expiry, user['id']))
            conn.commit()
            
            reset_url = url_for('reset_password', token=token, role=role, _external=True)
            body = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; letter-spacing: 0.5px;">Chennakesava Boys Hostel</h1>
                    <p style="color: #bfdbfe; margin: 10px 0 0 0; font-size: 16px;">Password Reset Request</p>
                </div>
                
                <div style="padding: 40px 30px; background-color: #ffffff;">
                    <p style="font-size: 16px; color: #374151; margin-top: 0;">Dear <strong>{user['name']}</strong>,</p>
                    <p style="font-size: 16px; color: #4b5563; line-height: 1.6; margin-bottom: 30px;">
                        We received a request to reset the password associated with your hostel account. You can reset your password by clicking the secure link below:
                    </p>
                    
                    <div style="text-align: center; margin: 35px 0;">
                        <a href="{reset_url}" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);">Reset My Password</a>
                    </div>
                    
                    <p style="font-size: 14px; color: #6b7280; line-height: 1.6; margin-top: 30px; border-top: 1px solid #f3f4f6; padding-top: 20px;">
                        <em>Security Notice: If you did not request a password reset, please ignore this email or contact hostel administration if you have concerns about your account's security.</em>
                    </p>
                </div>
                
                <div style="background-color: #f8fafc; padding: 25px 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #475569; font-weight: 600;">Need Assistance?</p>
                    <p style="margin: 0 0 15px 0; font-size: 14px; color: #64748b;">Contact Support: <strong>+91 9063748907</strong></p>
                    <p style="margin: 0; font-size: 12px; color: #94a3b8;">&copy; {datetime.now().year} Chennakesava Boys Hostel. All rights reserved.</p>
                </div>
            </div>
            """
            if send_auth_email(email, "Password Reset", body):
                flash("A password reset link has been sent to your email.", "success")
            else:
                flash("Failed to send email. Please check the server configuration or try again later.", "error")
        else:
            flash("If that email is registered, you will receive a reset link.", "info")
            
        cursor.close()
        conn.close()
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

# ============================================================
# ROUTE: Reset Password
# ============================================================
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        token = request.args.get('token')
        role = request.args.get('role', 'student')
        if not token:
            flash("Invalid or missing reset token.", "error")
            return redirect(url_for('login'))
        return render_template('reset_password.html', token=token, role=role)
        
    if request.method == 'POST':
        token = request.form.get('token')
        role = request.form.get('role', 'student')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', token=token, role=role)
            
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        table = 'admins' if role == 'admin' else 'students'
        
        cursor.execute(f"SELECT id FROM {table} WHERE reset_token=%s AND reset_token_expiry > NOW()", (token,))
        user = cursor.fetchone()
        
        if user:
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            cursor.execute(f"UPDATE {table} SET password_hash=%s, reset_token=NULL, reset_token_expiry=NULL, must_change_password=FALSE WHERE id=%s", 
                           (hashed, user['id']))
            conn.commit()
            flash("Your password has been reset successfully! You can now log in.", "success")
        else:
            flash("The reset link is invalid or has expired.", "error")
            
        cursor.close()
        conn.close()
        return redirect(url_for('login'))

# ============================================================
# ROUTE: Change Password (Internal)
# ============================================================
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if not is_logged_in():
        return redirect(url_for('login'))
        
    must_change = session.get('must_change', False)
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash("New passwords do not match.", "error")
            return render_template('change_password.html', must_change=must_change)
            
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        table = 'admins' if is_admin() else 'students'
        
        cursor.execute(f"SELECT password_hash FROM {table} WHERE id=%s", (session['user_id'],))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(current_password.encode(), user['password_hash'].encode()):
            hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            cursor.execute(f"UPDATE {table} SET password_hash=%s, must_change_password=FALSE WHERE id=%s", 
                           (hashed, session['user_id']))
            conn.commit()
            session.pop('must_change', None)
            
            # Send Professional Password Change Email
            user_email = session.get('user_email')
            user_name = session.get('user_name')
            now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            body = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; letter-spacing: 0.5px;">Chennakesava Boys Hostel</h1>
                    <p style="color: #bfdbfe; margin: 10px 0 0 0; font-size: 16px;">Security Confirmation</p>
                </div>
                
                <div style="padding: 40px 30px; background-color: #ffffff;">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <div style="display: inline-block; background-color: #dcfce7; padding: 15px; border-radius: 50%;">
                            <span style="font-size: 32px;">✅</span>
                        </div>
                        <h2 style="color: #166534; margin: 15px 0 0 0; font-size: 22px;">Password Changed Successfully</h2>
                    </div>
                    
                    <p style="font-size: 16px; color: #374151;">Dear <strong>{user_name}</strong>,</p>
                    <p style="font-size: 16px; color: #4b5563; line-height: 1.6; margin-bottom: 25px;">
                        This official notice is to confirm that the password for your hostel portal account has been successfully updated.
                    </p>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 25px 0; border: 1px solid #e2e8f0; border-left: 4px solid #10b981;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 6px 0; color: #64748b; font-size: 14px; width: 120px;">Account Email:</td>
                                <td style="padding: 6px 0; color: #1e293b; font-size: 15px; font-weight: 600;">{user_email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 6px 0; color: #64748b; font-size: 14px;">Date & Time:</td>
                                <td style="padding: 6px 0; color: #1e293b; font-size: 15px; font-weight: 600;">{now_time}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #fef2f2; padding: 15px 20px; border-radius: 6px; border-left: 4px solid #ef4444; margin-top: 30px;">
                        <p style="font-size: 14px; color: #991b1b; margin: 0; line-height: 1.5;">
                            <strong>Security Alert:</strong> If you did not authorize this password change, please contact the hostel administration <strong>immediately</strong> to secure your account and prevent unauthorized access.
                        </p>
                    </div>
                </div>
                
                <div style="background-color: #f8fafc; padding: 25px 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #475569; font-weight: 600;">Need Assistance?</p>
                    <p style="margin: 0 0 15px 0; font-size: 14px; color: #64748b;">Contact Support: <strong>+91 9063748907</strong></p>
                    <p style="margin: 0; font-size: 12px; color: #94a3b8;">&copy; {datetime.now().year} Chennakesava Boys Hostel. All rights reserved.</p>
                </div>
            </div>
            """
            send_auth_email(user_email, "Security Alert: Password Changed", body)
            
            flash("Password updated successfully!", "success")
            cursor.close()
            conn.close()
            return redirect(url_for('index'))
        else:
            flash("Current password is incorrect.", "error")
            
        cursor.close()
        conn.close()
        
    return render_template('change_password.html', must_change=must_change)

# ============================================================
# ROUTE: Logout
# ============================================================
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

# ============================================================
# ROUTE: Register Student (Admin only)
# ============================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if not is_admin():
        flash("Admin access required.", "error")
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms WHERE status != 'maintenance' ORDER BY room_number")
    rooms = cursor.fetchall()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('new_student_email') or request.form.get('email', '')
        email = email.strip()
        
        password = request.form.get('new_student_password') or request.form.get('password', '')
        password = password.strip()
        
        mobile_number = request.form.get('mobile_number', '').strip()
        parent_number = request.form.get('parent_number', '').strip()
        roll_number = request.form.get('roll_number', '').strip()
        course = request.form.get('course', '').strip()
        year_of_study = request.form.get('year_of_study', 1)
        room_id = request.form.get('room_id') or None
        
        # New Fields
        dob = request.form.get('dob') or None
        gender = request.form.get('gender', '').strip()
        aadhaar_number = request.form.get('aadhaar_number', '').strip()
        blood_group = request.form.get('blood_group', '').strip()
        parent_name = request.form.get('parent_name', '').strip()
        parent_relation = request.form.get('parent_relation', '').strip()
        college_name = request.form.get('college_name', '').strip()
        branch = request.form.get('branch', '').strip()
        permanent_address = request.form.get('permanent_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        pincode = request.form.get('pincode', '').strip()

        if not name or not email or not password:
            flash("Name, email and password are required.", "error")
            cursor.close(); conn.close()
            return render_template('register.html', rooms=rooms)

        # Hash the password
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            cursor.execute(
                """INSERT INTO students (name, email, password_hash, mobile_number, parent_number, roll_number, 
course, year_of_study, room_id, dob, gender, aadhaar_number, blood_group, parent_name, parent_relation, college_name, branch, permanent_address, city, state, pincode, must_change_password)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)""",
                (name, email, hashed, mobile_number, parent_number, roll_number, course, year_of_study, room_id,
                 dob, gender, aadhaar_number, blood_group, parent_name, parent_relation, college_name, branch, permanent_address, city, state, pincode)
            )
            student_id = cursor.lastrowid

            # Update room occupancy if room assigned
            if room_id:
                cursor.execute(
                    "UPDATE rooms SET current_occupancy = current_occupancy + 1 WHERE id = %s", (room_id,)
                )
                # Update room status if full
                cursor.execute(
                    "UPDATE rooms SET status = IF(current_occupancy >= capacity, 'full', 'available') WHERE id = %s",
                    (room_id,)
                )

            # Create initial fee record for current month
            today = date.today()
            month_name = today.strftime("%B %Y")
            due = today.replace(day=10)  # Due on 10th of the month
            if room_id:
                cursor.execute("SELECT monthly_fee FROM rooms WHERE id = %s", (room_id,))
                room = cursor.fetchone()
                fee_amount = room['monthly_fee'] if room else 5000.00
            else:
                fee_amount = 5000.00

            cursor.execute(
                "INSERT INTO fees (student_id, amount, month, year, due_date) VALUES (%s, %s, %s, %s, %s)",
                (student_id, fee_amount, month_name, today.year, due)
            )

            login_url = url_for('login', _external=True)
            body = f"""
            <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 35px 20px; text-align: center;">
                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 0.5px;">Chennakesava Boys Hostel</h1>
                    <p style="color: #bfdbfe; margin: 10px 0 0 0; font-size: 18px; font-weight: 500;">Welcome to Your New Home!</p>
                </div>
                
                <div style="padding: 40px 30px; background-color: #ffffff;">
                    <p style="font-size: 16px; color: #374151; margin-top: 0;">Dear <strong>{name}</strong>,</p>
                    <p style="font-size: 16px; color: #4b5563; line-height: 1.6; margin-bottom: 25px;">
                        We are thrilled to welcome you to Chennakesava Boys Hostel. Your official student portal account has been successfully generated by the administration.
                    </p>
                    <p style="font-size: 16px; color: #4b5563; line-height: 1.6; margin-bottom: 30px;">
                        Through your student portal, you will be able to effortlessly manage your profile, track and pay your monthly hostel fees securely, and submit maintenance or food complaints directly to the management team.
                    </p>
                    
                    <div style="background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 25px; border-radius: 8px; margin: 30px 0; position: relative;">
                        <div style="position: absolute; top: -12px; left: 20px; background-color: #2563eb; color: white; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; letter-spacing: 0.5px;">YOUR LOGIN CREDENTIALS</div>
                        <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px; width: 100px;">Email ID:</td>
                                <td style="padding: 8px 0; color: #0f172a; font-size: 16px; font-weight: 600;">{email}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; color: #64748b; font-size: 14px;">Password:</td>
                                <td style="padding: 8px 0;">
                                    <span style="background-color: #e2e8f0; color: #0f172a; padding: 4px 10px; border-radius: 4px; font-family: monospace; font-size: 16px; font-weight: 700; letter-spacing: 1px;">{password}</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #fffbeb; padding: 15px 20px; border-radius: 6px; border-left: 4px solid #f59e0b; margin-bottom: 35px;">
                        <p style="font-size: 14px; color: #b45309; margin: 0; line-height: 1.5;">
                            <strong>Security Action Required:</strong> For your personal safety, our system has flagged your account. You will be strictly required to change this temporary password immediately during your first login attempt.
                        </p>
                    </div>
                    
                    <div style="text-align: center; margin: 40px 0 10px 0;">
                        <a href="{login_url}" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 6px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); transition: all 0.3s ease;">Access Student Portal</a>
                    </div>
                </div>
                
                <div style="background-color: #f8fafc; padding: 25px 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 0 0 10px 0; font-size: 14px; color: #475569; font-weight: 600;">Need Assistance?</p>
                    <p style="margin: 0 0 15px 0; font-size: 14px; color: #64748b;">Contact Support: <strong>+91 9063748907</strong></p>
                    <p style="margin: 0; font-size: 12px; color: #94a3b8;">&copy; {today.year} Chennakesava Boys Hostel. All rights reserved.</p>
                </div>
            </div>
            """
            if send_auth_email(email, "Welcome to Chennakesava Boys Hostel!", body):
                flash(f"Student '{name}' registered successfully! A welcome email was sent.", "success")
            else:
                flash(f"Student '{name}' registered, but the email failed to send. Please check your SMTP configuration.", "error")

            cursor.close(); conn.close()
            return redirect(url_for('admin_dashboard'))

        except mysql.connector.IntegrityError as e:
            conn.rollback()
            error_msg = str(e).replace('\n', ' | ')
            db_engine = "MySQL"
            conn_host = DB_CONFIG.get('host', 'unknown')
            conn_db = DB_CONFIG.get('database', 'unknown')
            
            trace_log = (
                f"🚨 [TRACE DBG] ENGINE: {db_engine} | HOST: {conn_host} | DB: {conn_db} | "
                f"ERRNO: {getattr(e, 'errno', 'N/A')} | SQLSTATE: {getattr(e, 'sqlstate', 'N/A')} | "
                f"MSG: {error_msg}"
            )
                
            flash(trace_log, "error")
            # Also print to terminal for server logs
            print(trace_log)

    cursor.close()
    conn.close()
    return render_template('register.html', rooms=rooms)

# ============================================================
# ROUTE: Student Dashboard
# ============================================================
@app.route('/student/dashboard')
def student_dashboard():
    if not is_student():
        flash("Please login as a student.", "error")
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get student details with room info
    cursor.execute("""
        SELECT s.*, r.room_number, r.floor, r.room_type, r.monthly_fee
        FROM students s
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE s.id = %s
    """, (session['user_id'],))
    student = cursor.fetchone()

    # Get latest fee records
    cursor.execute("""
        SELECT * FROM fees WHERE student_id = %s ORDER BY year DESC, id DESC LIMIT 6
    """, (session['user_id'],))
    fees = cursor.fetchall()

    # Get student's fee receipts
    cursor.execute("""
        SELECT * FROM fee_receipts WHERE student_id = %s ORDER BY created_at DESC
    """, (session['user_id'],))
    receipts = cursor.fetchall()

    # Get student's complaints
    cursor.execute("""
        SELECT * FROM complaints WHERE student_id = %s ORDER BY submitted_at DESC
    """, (session['user_id'],))
    complaints = cursor.fetchall()

    # Get roommate details
    roommates = []
    if student and student['room_id']:
        cursor.execute("""
            SELECT name, email, mobile_number, course, year_of_study 
            FROM students 
            WHERE room_id = %s AND id != %s AND status = 'active'
        """, (student['room_id'], session['user_id']))
        roommates = cursor.fetchall()

    # Get student's activity logs
    cursor.execute("""
        SELECT * FROM student_activity_logs WHERE student_id = %s ORDER BY created_at DESC LIMIT 15
    """, (session['user_id'],))
    activity_logs = cursor.fetchall()

    # Get active notices
    cursor.execute("""
        SELECT n.*, a.name as admin_name FROM notices n
        JOIN admins a ON n.posted_by = a.id
        WHERE n.is_active = TRUE ORDER BY n.created_at DESC LIMIT 10
    """)
    notices = cursor.fetchall()

    # --- FOOD MANAGEMENT ---
    today_str = date.today().isoformat()
    
    # 1. Fetch Today's Menu
    cursor.execute("""
        SELECT * FROM daily_menus WHERE date = %s
    """, (today_str,))
    todays_menu = cursor.fetchall()
    
    # 2. Fetch Today's Opt-out status
    cursor.execute("""
        SELECT * FROM food_optouts WHERE student_id = %s AND date = %s
    """, (session['user_id'], today_str))
    optout = cursor.fetchone()
    if not optout:
        optout = {'breakfast': 0, 'lunch': 0, 'dinner': 0, 'reason': ''}

    # Calculate days in hostel
    days_in_hostel = 0
    if student and student.get('created_at'):
        delta = datetime.now() - student['created_at']
        days_in_hostel = delta.days

    cursor.close()
    conn.close()

    return render_template('student_dashboard.html',
                           student=student,
                           roommates=roommates,
                           activity_logs=activity_logs,
                           fees=fees,
                           receipts=receipts,
                           complaints=complaints,
                           notices=notices,
                           todays_menu=todays_menu,
                           optout=optout,
                           today_str=today_str,
                           days_in_hostel=days_in_hostel)

# ============================================================
# ROUTE: Add Food Opt-out (Student)
# ============================================================
@app.route('/student/food/optout', methods=['POST'])
def student_food_optout():
    if not is_student():
        return jsonify({'error': 'Unauthorized'}), 401
    
    date_str = request.form.get('date')
    reason = request.form.get('reason', '')
    
    # Checkboxes only arrive if checked
    skip_b = 1 if request.form.get('skip_breakfast') else 0
    skip_l = 1 if request.form.get('skip_lunch') else 0
    skip_d = 1 if request.form.get('skip_dinner') else 0
    
    today = date.today().isoformat()
    
    if date_str != today:
        flash("You can only change opt-outs for today.", "error")
        return redirect(url_for('student_dashboard'))
        
    now = datetime.now()
    hour = now.hour
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get existing to check time bounds
    cursor.execute("SELECT * FROM food_optouts WHERE student_id = %s AND date = %s", (session['user_id'], date_str))
    existing = cursor.fetchone()
    
    old_b = existing['breakfast'] if existing else 0
    old_l = existing['lunch'] if existing else 0
    old_d = existing['dinner'] if existing else 0
    
    # Deadline rules: Breakfast cutoff 7 AM, Lunch/Dinner cutoff 10 AM
    if skip_b != old_b and hour >= 7:
        flash("Breakfast opt-out deadline (7 AM) has passed.", "error")
        cursor.close(); conn.close()
        return redirect(url_for('student_dashboard'))
    
    if (skip_l != old_l or skip_d != old_d) and hour >= 10:
        flash("Lunch/Dinner opt-out deadline (10 AM) has passed.", "error")
        cursor.close(); conn.close()
        return redirect(url_for('student_dashboard'))
        
    if existing:
        cursor.execute("""
            UPDATE food_optouts 
            SET breakfast = %s, lunch = %s, dinner = %s, reason = %s 
            WHERE id = %s
        """, (skip_b, skip_l, skip_d, reason, existing['id']))
    else:
        cursor.execute("""
            INSERT INTO food_optouts (student_id, date, breakfast, lunch, dinner, reason) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (session['user_id'], date_str, skip_b, skip_l, skip_d, reason))
        
    conn.commit()
    cursor.close()
    conn.close()
    
    flash("Opt-out preferences saved successfully!", "success")
    return redirect(url_for('student_dashboard'))
@app.route('/complaints/submit', methods=['POST'])
def submit_complaint():
    if not is_student():
        return jsonify({'error': 'Unauthorized'}), 401

    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'other')

    if not title or not description:
        flash("Title and description are required.", "error")
        return redirect(url_for('student_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO complaints (student_id, title, description, category) VALUES (%s, %s, %s, %s)",
        (session['user_id'], title, description, category)
    )
    cursor.close()
    conn.close()
    
    log_activity(session['user_id'], f"Submitted complaint: {title}")

    flash("Complaint submitted successfully!", "success")
    return redirect(url_for('student_dashboard'))

# ============================================================
# ROUTE: Admin Dashboard
# ============================================================
@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():
        flash("Admin access required.", "error")
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Summary counts
    cursor.execute("SELECT COUNT(*) as total FROM students WHERE status='active'")
    total_students = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM rooms WHERE status='available'")
    available_rooms = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM complaints WHERE status='open'")
    open_complaints = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM fees WHERE status='pending'")
    pending_fees = cursor.fetchone()['total']

    # All students with room info
    cursor.execute("""
        SELECT s.*, r.room_number FROM students s
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE s.status = 'active'
        ORDER BY s.created_at DESC
    """)
    students = cursor.fetchall()
    recent_students = students[:5]

    # Fee Summary stats
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM fee_receipts")
    total_collected_fees = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM fee_receipts")
    total_receipts = cursor.fetchone()['total']

    # All rooms
    cursor.execute("SELECT * FROM rooms ORDER BY room_number")
    rooms = cursor.fetchall()

    # All complaints with student names
    cursor.execute("""
        SELECT c.*, s.name as student_name, s.roll_number, r.room_number
        FROM complaints c
        JOIN students s ON c.student_id = s.id
        LEFT JOIN rooms r ON s.room_id = r.id
        ORDER BY c.submitted_at DESC
    """)
    complaints = cursor.fetchall()

    # All notices
    cursor.execute("""
        SELECT n.*, a.name as admin_name FROM notices n
        JOIN admins a ON n.posted_by = a.id
        ORDER BY n.created_at DESC
    """)
    notices = cursor.fetchall()

    # Recent fees
    cursor.execute("""
        SELECT f.*, s.name as student_name FROM fees f
        JOIN students s ON f.student_id = s.id
        ORDER BY f.created_at DESC LIMIT 20
    """)
    fees = cursor.fetchall()
    
    # SMS Logs
    cursor.execute("""
        SELECT l.*, s.name as student_name FROM sms_logs l
        LEFT JOIN students s ON l.student_id = s.id
        ORDER BY l.sent_at DESC LIMIT 30
    """)
    sms_logs = cursor.fetchall()

    # Settings
    cursor.execute("SELECT setting_value FROM settings WHERE setting_key = 'fast2sms_api_key'")
    setting_row = cursor.fetchone()
    fast2sms_api_key = setting_row['setting_value'] if setting_row else ""

    # --- FOOD MANAGEMENT STATS ---
    today_str = date.today().isoformat()
    
    # Total Active Students separated by meal preference
    cursor.execute("SELECT COUNT(*) as c FROM students WHERE status='active' AND meal_preference='veg'")
    tot_veg = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM students WHERE status='active' AND meal_preference='non-veg'")
    tot_nonveg = cursor.fetchone()['c']

    # Opt-outs for today
    cursor.execute("""
        SELECT f.*, s.name, s.roll_number, s.meal_preference
        FROM food_optouts f
        JOIN students s ON f.student_id = s.id
        WHERE f.date = %s
    """, (today_str,))
    optouts = cursor.fetchall()
    
    # Calculate Expected Count
    optB = 0; optL = 0; optD = 0
    optB_veg = 0; optB_nonveg = 0
    optL_veg = 0; optL_nonveg = 0
    optD_veg = 0; optD_nonveg = 0

    for o in optouts:
        pref = o['meal_preference']
        if o['breakfast']:
            optB += 1
            if pref == 'veg': optB_veg += 1 
            else: optB_nonveg += 1
        if o['lunch']:
            optL += 1
            if pref == 'veg': optL_veg += 1 
            else: optL_nonveg += 1
        if o['dinner']:
            optD += 1
            if pref == 'veg': optD_veg += 1 
            else: optD_nonveg += 1

    expected_counts = {
        'total_veg': tot_veg,
        'total_nonveg': tot_nonveg,
        'breakfast': {'opt': optB, 'veg': tot_veg - optB_veg, 'nonveg': tot_nonveg - optB_nonveg},
        'lunch': {'opt': optL, 'veg': tot_veg - optL_veg, 'nonveg': tot_nonveg - optL_nonveg},
        'dinner': {'opt': optD, 'veg': tot_veg - optD_veg, 'nonveg': tot_nonveg - optD_nonveg}
    }
    
    # Today's Menu
    cursor.execute("SELECT * FROM daily_menus WHERE date = %s", (today_str,))
    todays_menu = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_dashboard.html',
                           total_students=total_students,
                           available_rooms=available_rooms,
                           open_complaints=open_complaints,
                           pending_fees=pending_fees,
                           total_collected_fees=total_collected_fees,
                           total_receipts=total_receipts,
                           recent_students=recent_students,
                           students=students,
                           rooms=rooms,
                           complaints=complaints,
                           notices=notices,
                           fees=fees,
                           sms_logs=sms_logs,
                           fast2sms_api_key=fast2sms_api_key,
                           todays_menu=todays_menu,
                           optouts=optouts,
                           expected_counts=expected_counts,
                           today_str=today_str)

# ============================================================
# ROUTE: Update Food Menu (Admin)
# ============================================================
@app.route('/admin/food/menu', methods=['POST'])
def admin_food_menu():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
        
    date_str = request.form.get('date')
    meal_slot = request.form.get('meal_slot')
    meal_type = request.form.get('meal_type')
    items = request.form.get('items', '').strip()
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Check if locked
    cursor.execute("SELECT is_locked FROM daily_menus WHERE date = %s AND meal_slot = %s AND meal_type = %s",
                   (date_str, meal_slot, meal_type))
    existing = cursor.fetchone()
    
    if existing and existing['is_locked']:
        flash(f"Cannot edit {meal_slot} menu. It is already locked.", "error")
    else:
        if existing:
            cursor.execute("""
                UPDATE daily_menus SET items = %s WHERE date = %s AND meal_slot = %s AND meal_type = %s
            """, (items, date_str, meal_slot, meal_type))
        else:
            cursor.execute("""
                INSERT INTO daily_menus (date, meal_slot, meal_type, items) VALUES (%s, %s, %s, %s)
            """, (date_str, meal_slot, meal_type, items))
        conn.commit()
        flash("Menu saved successfully!", "success")
        
    cursor.close()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/food/menu/edit/<int:id>', methods=['POST'])
def edit_food_menu(id):
    """
    1. Edit a menu item (update the food items text)
    3. Edit is locked after cutoff time (7AM for breakfast, 10AM for lunch/dinner)
    """
    if not is_admin(): return redirect(url_for('login'))
    items = request.form.get('items', '').strip()
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM daily_menus WHERE id = %s", (id,))
    menu = cursor.fetchone()
    
    if not menu:
        flash("Menu not found.", "error")
    elif menu['is_locked']:
        flash(f"Cannot edit {menu['meal_slot']}. It is locked.", "error")
    else:
        hour = datetime.now().hour
        if menu['meal_slot'] == 'breakfast' and hour >= 7:
            flash("Breakfast edit cutoff (7 AM) has passed.", "error")
        elif menu['meal_slot'] in ['lunch', 'dinner'] and hour >= 10:
            flash(f"{menu['meal_slot'].title()} edit cutoff (10 AM) has passed.", "error")
        else:
            cursor.execute("UPDATE daily_menus SET items = %s WHERE id = %s", (items, id))
            conn.commit()
            flash("Menu item updated.", "success")
            
    cursor.close(); conn.close()
    return redirect(url_for('admin_dashboard') + '#food')

@app.route('/admin/food/menu/delete/<int:id>', methods=['POST'])
def delete_food_menu(id):
    """
    2. Delete a menu item
    3. Delete applies same cutoff lock logic as edit
    """
    if not is_admin(): return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM daily_menus WHERE id = %s", (id,))
    menu = cursor.fetchone()
    
    if not menu:
        flash("Menu not found.", "error")
    elif menu['is_locked']:
        flash(f"Cannot delete {menu['meal_slot']}. It is locked.", "error")
    else:
        hour = datetime.now().hour
        if menu['meal_slot'] == 'breakfast' and hour >= 7:
            flash("Breakfast delete cutoff (7 AM) has passed.", "error")
        elif menu['meal_slot'] in ['lunch', 'dinner'] and hour >= 10:
            flash(f"{menu['meal_slot'].title()} delete cutoff (10 AM) has passed.", "error")
        else:
            cursor.execute("DELETE FROM daily_menus WHERE id = %s", (id,))
            conn.commit()
            flash("Menu item deleted.", "success")
            
    cursor.close(); conn.close()
    return redirect(url_for('admin_dashboard') + '#food')

# ============================================================
# ROUTE: Add Notice (Admin)
# ============================================================
@app.route('/notices/add', methods=['POST'])
def add_notice():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'medium')

    if not title or not content:
        flash("Title and content are required.", "error")
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notices (title, content, priority, posted_by) VALUES (%s, %s, %s, %s)",
        (title, content, priority, session['user_id'])
    )
    cursor.close()
    conn.close()

    flash("Notice posted successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ============================================================
# ROUTE: Update Complaint Status (Admin)
# ============================================================
@app.route('/complaints/update/<int:complaint_id>', methods=['POST'])
def update_complaint(complaint_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    status = request.form.get('status')
    admin_response = request.form.get('admin_response', '').strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE complaints SET status = %s, admin_response = %s WHERE id = %s",
        (status, admin_response, complaint_id)
    )
    cursor.close()
    conn.close()

    flash("Complaint updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ============================================================
# ROUTE: Update Fee Status (Admin)
# ============================================================
@app.route('/fees/update/<int:fee_id>', methods=['POST'])
def update_fee(fee_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    status = request.form.get('status')
    payment_date = date.today() if status == 'paid' else None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE fees SET status = %s, payment_date = %s WHERE id = %s",
        (status, payment_date, fee_id)
    )
    cursor.close()
    conn.close()

    flash("Fee status updated!", "success")
    return redirect(url_for('admin_dashboard'))

# ============================================================
# ROUTE: Assign Room to Student (Admin)
# ============================================================
@app.route('/students/assign-room/<int:student_id>', methods=['POST'])
def assign_room(student_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    new_room_id = request.form.get('room_id') or None

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get current room
    cursor.execute("SELECT room_id FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    old_room_id = student['room_id'] if student else None

    # Decrease old room occupancy
    if old_room_id:
        cursor.execute(
            "UPDATE rooms SET current_occupancy = GREATEST(0, current_occupancy - 1), status = 'available' WHERE id = %s",
            (old_room_id,)
        )

    # Assign new room
    cursor.execute("UPDATE students SET room_id = %s WHERE id = %s", (new_room_id, student_id))

    # Increase new room occupancy
    if new_room_id:
        cursor.execute(
            "UPDATE rooms SET current_occupancy = current_occupancy + 1 WHERE id = %s", (new_room_id,)
        )
        cursor.execute(
            "UPDATE rooms SET status = IF(current_occupancy >= capacity, 'full', 'available') WHERE id = %s",
            (new_room_id,)
        )

    cursor.close()
    conn.close()

    flash("Room assigned successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ============================================================
# ROUTE: Temporary Database Cleanup Endpoint (Admin)
# ============================================================
@app.route('/admin/force_cleanup', methods=['GET'])
def force_cleanup():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    email = request.args.get('email', '').strip()
    roll_number = request.args.get('roll_number', '').strip()

    if not email and not roll_number:
        return jsonify({'error': 'Please provide email or roll_number parameter.'}), 400

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    log = {"tables_checked": [], "records_deleted": {}, "status": "success"}

    try:
        # Check students table
        cursor.execute("SELECT id FROM students WHERE email = %s OR roll_number = %s", (email, roll_number))
        students = cursor.fetchall()
        if students:
            log['records_deleted']['students'] = len(students)
            for s in students:
                cursor.execute("DELETE FROM students WHERE id = %s", (s['id'],))
        else:
            log['records_deleted']['students'] = 0

        # Check users table in current DB
        if email:
            cursor.execute("SHOW TABLES LIKE 'users'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                users = cursor.fetchall()
                log['records_deleted']['users_hostel'] = len(users)
                if users:
                    cursor.execute("DELETE FROM users WHERE email = %s", (email,))

        # Check admins table
        if email:
            cursor.execute("SELECT id FROM admins WHERE email = %s", (email,))
            admins = cursor.fetchall()
            log['records_deleted']['admins'] = len(admins)
            if admins:
                cursor.execute("DELETE FROM admins WHERE email = %s", (email,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        log['status'] = "error"
        log['error_message'] = str(e)
    finally:
        cursor.close()
        conn.close()

    return jsonify(log)

# ============================================================
# ROUTE: Delete/Deactivate Student (Admin)
# ============================================================
@app.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Free up the room
    cursor.execute("SELECT room_id, email FROM students WHERE id = %s", (student_id,))
    student = cursor.fetchone()
    student_email = student['email'] if student else None
    
    if student and student['room_id']:
        cursor.execute(
            "UPDATE rooms SET current_occupancy = GREATEST(0, current_occupancy - 1), status = 'available' WHERE id = %s",
            (student['room_id'],)
        )

    # Hard delete student (will cascade to fees, complaints, etc.)
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    
    # Hard delete from users table (if used by external auth/PHP app)
    if student_email:
        # Check if users table exists in current DB
        cursor.execute("SHOW TABLES LIKE 'users'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM users WHERE email = %s", (student_email,))
            
        # Check if test database exists and has users table
        cursor.execute("SHOW DATABASES LIKE 'test'")
        if cursor.fetchone():
            cursor.execute("SHOW TABLES FROM test LIKE 'users'")
            if cursor.fetchone():
                cursor.execute("DELETE FROM test.users WHERE email = %s", (student_email,))

    conn.commit()
    cursor.close()
    conn.close()

    flash("Student removed successfully!", "success")
    return redirect(url_for('admin_dashboard'))

# ============================================================
# ROUTE: Add Room (Admin)
# ============================================================
@app.route('/rooms/add', methods=['POST'])
def add_room():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    room_number = request.form.get('room_number', '').strip()
    floor = request.form.get('floor', 1)
    capacity = request.form.get('capacity', 2)
    room_type = request.form.get('room_type', 'double')
    monthly_fee = request.form.get('monthly_fee', 5000.00)

    if not room_number:
        flash("Room number is required.", "error")
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO rooms (room_number, floor, capacity, room_type, monthly_fee) VALUES (%s, %s, %s, %s, %s)",
            (room_number, floor, capacity, room_type, monthly_fee)
        )
        flash(f"Room {room_number} added successfully!", "success")
    except mysql.connector.IntegrityError:
        flash("Room number already exists.", "error")
    cursor.close()
    conn.close()

    return redirect(url_for('admin_dashboard'))

# ============================================================
# API ROUTES (JSON) - For potential JS fetch usage
# ============================================================
@app.route('/api/students')
def api_students():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.id, s.name, s.email, s.roll_number, s.mobile_number, r.room_number
        FROM students s LEFT JOIN rooms r ON s.room_id = r.id
        WHERE s.status='active'
    """)
    students = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(students)

@app.route('/api/rooms')
def api_rooms():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms ORDER BY room_number")
    rooms = cursor.fetchall()
    cursor.close(); conn.close()
    return jsonify(rooms)

@app.route('/admin/student/edit-mobile', methods=['POST'])
def edit_student_mobile():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    student_id = request.form.get('student_id')
    mobile_number = request.form.get('mobile_number', '').strip()
    parent_number = request.form.get('parent_number', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET mobile_number=%s, parent_number=%s WHERE id=%s", (mobile_number, parent_number, student_id))
    conn.commit()
    cursor.close(); conn.close()
    
    flash("Mobile numbers updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/fee/set-due-date', methods=['POST'])
def set_due_date():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
        
    fee_id = request.form.get('fee_id')
    due_date_str = request.form.get('due_date')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE fees SET due_date=%s WHERE id=%s", (due_date_str, fee_id))
    conn.commit()
    cursor.close(); conn.close()
    
    flash("Fee due date updated!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sms/send-manual', methods=['POST'])
def send_manual_sms():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
        
    student_id = request.form.get('student_id')
    message = request.form.get('message', '').strip()
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT mobile_number, parent_number FROM students WHERE id=%s", (student_id,))
    student = cursor.fetchone()
    cursor.close(); conn.close()
    
    if student:
        numbers = student['mobile_number']
        if student['parent_number']:
            numbers += f",{student['parent_number']}"
            
        success = send_fast2sms(numbers, message, student_id=student_id)
        if success:
            flash("SMS sent successfully!", "success")
        else:
            flash("Failed to send SMS. Check your API key or Fast2SMS balance.", "error")
            
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/sms/settings', methods=['POST'])
def save_sms_settings():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
        
    api_key = request.form.get('fast2sms_api_key', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO settings (setting_key, setting_value) VALUES ('fast2sms_api_key', %s) ON DUPLICATE KEY UPDATE setting_value=%s", (api_key, api_key))
    conn.commit()
    cursor.close(); conn.close()
    
    flash("SMS Settings saved!", "success")
    return redirect(url_for('admin_dashboard') + '#sms')

# ============================================================
# NEW ADMIN CRUD ROUTES 
# ============================================================
@app.route('/notices/edit/<int:id>', methods=['POST'])
def edit_notice(id):
    if not is_admin(): return redirect(url_for('login'))
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    priority = request.form.get('priority', 'medium')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE notices SET title=%s, content=%s, priority=%s WHERE id=%s", (title, content, priority, id))
    conn.commit(); cursor.close(); conn.close()
    flash("Notice updated successfully.", "success")
    return redirect(url_for('admin_dashboard') + '#notices')

@app.route('/notices/delete/<int:id>', methods=['POST'])
def delete_notice(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM notices WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    flash("Notice deleted successfully.", "success")
    return redirect(url_for('admin_dashboard') + '#notices')

@app.route('/complaints/delete/<int:id>', methods=['POST'])
def delete_complaint(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM complaints WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    flash("Complaint deleted successfully.", "success")
    return redirect(url_for('admin_dashboard') + '#complaints')

@app.route('/students/edit-details/<int:id>', methods=['POST'])
def edit_student_details(id):
    if not is_admin(): return redirect(url_for('login'))
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    course = request.form.get('course', '').strip()
    year_of_study = request.form.get('year_of_study', 1)
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE students SET name=%s, email=%s, course=%s, year_of_study=%s WHERE id=%s", (name, email, course, year_of_study, id))
    conn.commit(); cursor.close(); conn.close()
    flash("Student details updated successfully.", "success")
    return redirect(url_for('admin_dashboard') + '#students')

@app.route('/admin/student/<int:id>')
def admin_student_profile(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT s.*, r.room_number FROM students s LEFT JOIN rooms r ON s.room_id = r.id WHERE s.id=%s", (id,))
    student = cursor.fetchone()
    if not student:
        cursor.close(); conn.close()
        flash("Student not found", "error"); return redirect(url_for('admin_dashboard'))
    
    cursor.execute("SELECT * FROM fees WHERE student_id=%s ORDER BY created_at DESC", (id,))
    fees = cursor.fetchall()
    cursor.execute("SELECT * FROM complaints WHERE student_id=%s ORDER BY submitted_at DESC", (id,))
    complaints = cursor.fetchall()
    cursor.execute("SELECT * FROM student_activity_logs WHERE student_id=%s ORDER BY created_at DESC", (id,))
    activity_logs = cursor.fetchall()
    cursor.close(); conn.close()
    
    return render_template('admin_student_profile.html', student=student, fees=fees, complaints=complaints, activity_logs=activity_logs)

@app.route('/rooms/edit/<int:id>', methods=['POST'])
def edit_room(id):
    if not is_admin(): return redirect(url_for('login'))
    room_number = request.form.get('room_number', '').strip()
    floor = request.form.get('floor', 1)
    capacity = request.form.get('capacity', 2)
    room_type = request.form.get('room_type', 'double')
    monthly_fee = request.form.get('monthly_fee', 5000)
    
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE rooms SET room_number=%s, floor=%s, capacity=%s, room_type=%s, monthly_fee=%s WHERE id=%s", 
                   (room_number, floor, capacity, room_type, monthly_fee, id))
    conn.commit(); cursor.close(); conn.close()
    flash("Room updated successfully.", "success")
    return redirect(url_for('admin_dashboard') + '#rooms')

@app.route('/rooms/delete/<int:id>', methods=['POST'])
def delete_room(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db(); cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT current_occupancy FROM rooms WHERE id=%s", (id,))
    room = cursor.fetchone()
    if room and room['current_occupancy'] > 0:
        cursor.close(); conn.close()
        flash("Cannot delete a room that still has occupants!", "error")
        return redirect(url_for('admin_dashboard') + '#rooms')
    
    cursor.execute("DELETE FROM rooms WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    flash("Room deleted successfully.", "success")
    return redirect(url_for('admin_dashboard') + '#rooms')

@app.route('/fees/edit-details/<int:id>', methods=['POST'])
def edit_fee_details(id):
    if not is_admin(): return redirect(url_for('login'))
    amount = request.form.get('amount')
    due_date = request.form.get('due_date')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE fees SET amount=%s, due_date=%s WHERE id=%s", (amount, due_date, id))
    conn.commit(); cursor.close(); conn.close()
    flash("Fee details updated.", "success")
    return redirect(url_for('admin_dashboard') + '#fees')

@app.route('/fees/delete/<int:id>', methods=['POST'])
def delete_fee(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM fees WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    flash("Fee record deleted.", "success")
    return redirect(url_for('admin_dashboard') + '#fees')

# ============================================================
# FINANCE TRACKER ROUTES
# ============================================================
@app.route('/admin/finance')
def admin_finance():
    if not is_admin(): return redirect(url_for('login'))
    
    month_filter = request.args.get('month', date.today().strftime('%Y-%m'))
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    # Get all transactions for the filtered month
    cursor.execute("""
        SELECT * FROM transactions 
        WHERE DATE_FORMAT(date, '%Y-%m') = %s 
        ORDER BY date DESC, id DESC
    """, (month_filter,))
    transactions = cursor.fetchall()
    
    # Calculate summaries
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'Income')
    total_expense = sum(t['amount'] for t in transactions if t['type'] == 'Expense')
    profit_loss = total_income - total_expense
    
    # Calculate for chart
    cursor.execute("""
        SELECT DATE_FORMAT(date, '%%d') as day, type, SUM(amount) as total
        FROM transactions
        WHERE DATE_FORMAT(date, '%%Y-%%m') = %s
        GROUP BY day, type
    """, (month_filter,))
    chart_data_raw = cursor.fetchall()
    
    chart_data = {'days': [], 'income': [], 'expense': []}
    if chart_data_raw:
        days = sorted(list(set(r['day'] for r in chart_data_raw)))
        chart_data['days'] = days
        for d in days:
            inc = sum(r['total'] for r in chart_data_raw if r['day'] == d and r['type'] == 'Income')
            exp = sum(r['total'] for r in chart_data_raw if r['day'] == d and r['type'] == 'Expense')
            chart_data['income'].append(float(inc))
            chart_data['expense'].append(float(exp))
            
    cursor.close(); conn.close()
    
    return render_template('finance.html', 
                           transactions=transactions, 
                           total_income=total_income, 
                           total_expense=total_expense, 
                           profit_loss=profit_loss,
                           current_month=month_filter,
                           chart_data=chart_data)

@app.route('/admin/finance/add', methods=['POST'])
def add_finance_transaction():
    if not is_admin(): return redirect(url_for('login'))
    
    t_date = request.form.get('date')
    t_type = request.form.get('type')
    t_category = request.form.get('category')
    t_amount = request.form.get('amount')
    t_remarks = request.form.get('remarks', '')
    
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (date, type, category, amount, remarks) 
        VALUES (%s, %s, %s, %s, %s)
    """, (t_date, t_type, t_category, t_amount, t_remarks))
    conn.commit(); cursor.close(); conn.close()
    
    flash("Transaction added successfully.", "success")
    return redirect(url_for('admin_finance'))

@app.route('/admin/finance/edit/<int:id>', methods=['POST'])
def edit_finance_transaction(id):
    if not is_admin(): return redirect(url_for('login'))
    
    t_date = request.form.get('date')
    t_type = request.form.get('type')
    t_category = request.form.get('category')
    t_amount = request.form.get('amount')
    t_remarks = request.form.get('remarks', '')
    
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""
        UPDATE transactions 
        SET date=%s, type=%s, category=%s, amount=%s, remarks=%s 
        WHERE id=%s
    """, (t_date, t_type, t_category, t_amount, t_remarks, id))
    conn.commit(); cursor.close(); conn.close()
    
    flash("Transaction updated.", "success")
    return redirect(url_for('admin_finance') + f"?month={t_date[:7]}")

@app.route('/admin/finance/delete/<int:id>', methods=['POST'])
def delete_finance_transaction(id):
    if not is_admin(): return redirect(url_for('login'))
    
    month_filter = request.form.get('month', '')
    
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id=%s", (id,))
    conn.commit(); cursor.close(); conn.close()
    
    flash("Transaction deleted.", "success")
    return redirect(url_for('admin_finance') + (f"?month={month_filter}" if month_filter else ""))

# ============================================================
# NEW FEATURE: FEE RECEIPTS APIS
# ============================================================
@app.route('/api/students/<int:id>', methods=['GET'])
def api_get_student_info(id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT s.name, r.room_number 
        FROM students s 
        LEFT JOIN rooms r ON s.room_id = r.id 
        WHERE s.id = %s
    """, (id,))
    student = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if student:
        return jsonify({
            'name': student['name'],
            'room_number': student['room_number'] or ''
        })
    else:
        return jsonify({'error': 'Student not found'}), 404

@app.route('/api/receipts/create', methods=['POST'])
def api_create_receipt():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json or request.form
    student_id = data.get('student_id')
    student_name = data.get('student_name')
    room_number = data.get('room_number')
    amount = data.get('amount')
    payment_type = data.get('payment_type')
    payment_mode = data.get('payment_mode')
    period = data.get('period')
    remarks = data.get('remarks', '')

    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database error'}), 500

    cursor = conn.cursor(dictionary=True)
    
    try:
        # Insert record first to get the auto-increment ID
        cursor.execute("""
            INSERT INTO fee_receipts (student_id, student_name, room_number, amount, payment_type, payment_mode, period, remarks)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (student_id, student_name, room_number, amount, payment_type, payment_mode, period, remarks))
        
        new_id = cursor.lastrowid
        
        # Generate receipt_number and update the record
        receipt_number = f"RCP{new_id:03d}"
        cursor.execute("UPDATE fee_receipts SET receipt_number = %s WHERE id = %s", (receipt_number, new_id))
        
        conn.commit()
    except Exception as e:
        print("ERROR SAVING RECEIPT:", str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'message': 'Receipt created successfully', 'receipt_number': receipt_number}), 201

@app.route('/api/receipts/all', methods=['GET'])
def api_get_all_receipts():
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fee_receipts ORDER BY created_at DESC")
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(receipts)

@app.route('/api/receipts/student/<int:student_id>', methods=['GET'])
def api_get_student_receipts(student_id):
    if not (is_admin() or (is_student() and session.get('user_id') == student_id)):
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fee_receipts WHERE student_id = %s ORDER BY created_at DESC", (student_id,))
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(receipts)

@app.route('/api/student/receipts', methods=['GET'])
def api_get_my_receipts():
    if not is_student():
        return jsonify({'error': 'Unauthorized'}), 401
        
    student_id = session.get('user_id')
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fee_receipts WHERE student_id = %s ORDER BY created_at DESC", (student_id,))
    receipts = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify(receipts)

@app.route('/api/receipts/edit/<int:id>', methods=['PUT'])
def api_edit_receipt(id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.json or request.form
    amount = data.get('amount')
    payment_type = data.get('payment_type')
    payment_mode = data.get('payment_mode')
    period = data.get('period')
    remarks = data.get('remarks')
    
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE fee_receipts 
            SET amount=%s, payment_type=%s, payment_mode=%s, period=%s, remarks=%s 
            WHERE id=%s
        """, (amount, payment_type, payment_mode, period, remarks, id))
        conn.commit()
    except Exception as e:
        print("ERROR UPDATING RECEIPT:", str(e))
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
    
    return jsonify({'message': 'Receipt updated successfully'})

@app.route('/api/receipts/delete/<int:id>', methods=['DELETE'])
def api_delete_receipt(id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM fee_receipts WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'message': 'Receipt deleted successfully'})

@app.route('/api/receipts/download/<int:id>', methods=['GET'])
def api_download_receipt(id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT fr.*, s.roll_number, s.course, s.year_of_study 
        FROM fee_receipts fr
        LEFT JOIN students s ON fr.student_id = s.id
        WHERE fr.id = %s
    """, (id,))
    receipt = cursor.fetchone()
    cursor.close()
    conn.close()

    if not receipt:
        return jsonify({'error': 'Receipt not found'}), 404

    if not (is_admin() or (is_student() and session.get('user_id') == receipt['student_id'])):
        return jsonify({'error': 'Unauthorized'}), 401

    pdf = FPDF()
    pdf.add_page()
    
    # 1. Dark Navy Blue Header
    pdf.set_fill_color(26, 58, 107) # #1a3a6b
    pdf.rect(0, 0, 210, 35, style='F')
    
    # Header Left (CBH)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 24)
    pdf.set_xy(15, 10)
    pdf.cell(50, 10, txt="CBH")
    
    # Header Subtitle
    pdf.set_font("helvetica", '', 9)
    pdf.set_xy(15, 20)
    pdf.cell(100, 10, txt="CHENNAKESAVA BOYS HOSTEL")
    
    # Header Right (Contact)
    pdf.set_font("helvetica", '', 9)
    pdf.set_xy(140, 12)
    pdf.multi_cell(55, 5, txt="Warangal, Telangana\nPh: +91 9063748907", align='R')
    
    # 2. White bar with "FEE RECEIPT" and "Official Document"
    pdf.set_text_color(26, 58, 107)
    pdf.set_font("helvetica", 'B', 14)
    pdf.set_xy(15, 40)
    pdf.cell(100, 10, txt="F E E   R E C E I P T")
    
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("helvetica", '', 10)
    pdf.set_xy(120, 40)
    pdf.cell(75, 10, txt="Official Document", align='R')
    
    # 3. Thick orange line
    pdf.set_draw_color(232, 160, 32) # #e8a020
    pdf.set_line_width(1.5)
    pdf.line(10, 52, 200, 52)
    
    # 4. Receipt No & Date Row
    pdf.set_xy(15, 60)
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("helvetica", '', 9)
    pdf.cell(50, 5, txt="RECEIPT NO.")
    
    pdf.set_xy(150, 60)
    pdf.cell(45, 5, txt="DATE & TIME", align='R')
    
    pdf.set_xy(15, 65)
    pdf.set_text_color(26, 58, 107)
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(50, 8, txt=receipt['receipt_number'])
    
    # Format Date
    dt_str = receipt['created_at'].strftime('%d %b %Y') if receipt['created_at'] else ''
    tm_str = receipt['created_at'].strftime('%I:%M %p') if receipt['created_at'] else ''
    
    pdf.set_xy(150, 65)
    pdf.set_text_color(50, 50, 50)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(45, 6, txt=dt_str, align='R')
    pdf.set_xy(150, 71)
    pdf.set_font("helvetica", '', 10)
    pdf.cell(45, 6, txt=tm_str, align='R')
    
    # 5. STUDENT INFORMATION
    y_start = 90
    pdf.set_draw_color(232, 160, 32)
    pdf.set_line_width(1)
    pdf.line(15, y_start, 15, y_start+5)
    
    pdf.set_xy(18, y_start-1)
    pdf.set_text_color(26, 58, 107)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(100, 6, txt="STUDENT INFORMATION")
    
    y_grid = 100
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(15, y_grid, 180, 20, style='F')
    
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("helvetica", '', 10)
    pdf.set_xy(20, y_grid + 3)
    pdf.cell(40, 6, txt="Student Name")
    pdf.set_xy(105, y_grid + 3)
    pdf.cell(40, 6, txt="Roll Number")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_xy(60, y_grid + 3)
    pdf.cell(45, 6, txt=receipt['student_name'])
    pdf.set_xy(140, y_grid + 3)
    pdf.cell(45, 6, txt=receipt.get('roll_number') or 'N/A')
    
    y_grid += 10
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("helvetica", '', 10)
    pdf.set_xy(20, y_grid + 3)
    pdf.cell(40, 6, txt="Room Number")
    pdf.set_xy(105, y_grid + 3)
    pdf.cell(40, 6, txt="Course")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_xy(60, y_grid + 3)
    pdf.cell(45, 6, txt=str(receipt['room_number'] or 'N/A'))
    
    course_str = receipt.get('course') or 'N/A'
    if receipt.get('year_of_study'):
        course_str += f" Year {receipt['year_of_study']}"
    pdf.set_xy(140, y_grid + 3)
    pdf.cell(45, 6, txt=course_str)
    
    # 6. PAYMENT INFORMATION
    y_start = 135
    pdf.set_draw_color(232, 160, 32)
    pdf.set_line_width(1)
    pdf.line(15, y_start, 15, y_start+5)
    
    pdf.set_xy(18, y_start-1)
    pdf.set_text_color(26, 58, 107)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(100, 6, txt="PAYMENT INFORMATION")
    
    y_grid = 145
    pdf.set_fill_color(248, 249, 250)
    pdf.rect(15, y_grid, 180, 20, style='F')
    
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("helvetica", '', 10)
    pdf.set_xy(20, y_grid + 3)
    pdf.cell(40, 6, txt="Payment Type")
    pdf.set_xy(105, y_grid + 3)
    pdf.cell(40, 6, txt="Payment Mode")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_xy(60, y_grid + 3)
    pdf.cell(45, 6, txt=receipt['payment_type'])
    pdf.set_xy(140, y_grid + 3)
    pdf.cell(45, 6, txt=receipt['payment_mode'])
    
    y_grid += 10
    pdf.set_text_color(150, 150, 150)
    pdf.set_font("helvetica", '', 10)
    pdf.set_xy(20, y_grid + 3)
    pdf.cell(40, 6, txt="Period")
    pdf.set_xy(105, y_grid + 3)
    pdf.cell(40, 6, txt="Status")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", 'B', 10)
    pdf.set_xy(60, y_grid + 3)
    pdf.cell(45, 6, txt=receipt['period'])
    
    # PAID Badge
    pdf.set_fill_color(220, 245, 225) # light green
    pdf.rect(140, y_grid+3, 16, 6, style='F')
    pdf.set_text_color(30, 130, 70)
    pdf.set_font("helvetica", 'B', 9)
    pdf.set_xy(140, y_grid+3)
    pdf.cell(16, 6, txt="PAID", align='C')
    
    # 7. Total Amount Box
    y_box = 180
    pdf.set_fill_color(26, 58, 107)
    pdf.rect(15, y_box, 180, 22, style='F')
    
    pdf.set_text_color(150, 180, 220)
    pdf.set_font("helvetica", '', 12)
    pdf.set_xy(25, y_box + 6)
    pdf.cell(50, 10, txt="TOTAL AMOUNT PAID")
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", 'B', 24)
    amt_str = "Rs. " + "{:,.0f}".format(receipt['amount'])
    pdf.set_xy(120, y_box + 4)
    pdf.cell(70, 14, txt=amt_str, align='R')
    
    # 8. Signatures
    y_sig = 230
    pdf.set_draw_color(100, 100, 100)
    pdf.set_line_width(0.5)
    
    pdf.line(20, y_sig, 80, y_sig)
    pdf.line(130, y_sig, 190, y_sig)
    
    pdf.set_text_color(120, 120, 120)
    pdf.set_font("helvetica", '', 9)
    pdf.set_xy(20, y_sig + 2)
    pdf.cell(60, 5, txt="Student Signature", align='C')
    
    pdf.set_xy(130, y_sig + 2)
    pdf.cell(60, 5, txt="Authorized Signatory", align='C')
    
    # 9. Footer
    y_foot = 260
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, y_foot, 200, y_foot)
    
    pdf.set_xy(10, y_foot + 5)
    pdf.set_font("helvetica", '', 8)
    pdf.multi_cell(190, 4, txt="This is a computer generated receipt and does not require a physical signature.\nChennakesava Boys Hostel - Warangal, Telangana | +91 9063748907", align='C')

    filename = f"{receipt['receipt_number']}.pdf"
    filepath = os.path.join(app.config.get('UPLOAD_FOLDER', 'static'), filename)
    pdf.output(filepath)
    
    return send_file(filepath, as_attachment=True)

# ============================================================
# NEW JSON API FOR REACT FRONTEND
# ============================================================

import jwt

def api_require_student():
    # Verify session (if logged in via Flask)
    if 'user_id' in session and session.get('role') == 'student':
        return session['user_id']
    
    # Verify JWT from headers (if logged in via React SPA)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            # Match the JWT_SECRET from backend/.env
            decoded = jwt.decode(token, 'super_secret_jwt_key_for_hostel', algorithms=['HS256'])
            if decoded.get('role') == 'student' and 'id' in decoded:
                return decoded['id']
        except Exception as e:
            print("JWT decode failed:", e)
    
    return None

@app.before_request
def handle_options_request():
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        headers = None
        if 'Origin' in request.headers:
            headers = {
                'Access-Control-Allow-Origin': request.headers['Origin'],
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
                'Access-Control-Allow-Credentials': 'true'
            }
        if headers:
            for key, value in headers.items():
                response.headers[key] = value
        return response

@app.route('/api/student/profile', methods=['GET'])
def api_student_profile():
    student_id = api_require_student()
    if not student_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT s.id, s.name, s.email, s.mobile_number, s.course, s.year_of_study, s.roll_number, s.status,
               r.room_number, r.floor, r.room_type, r.monthly_fee
        FROM students s
        LEFT JOIN rooms r ON s.room_id = r.id
        WHERE s.id = %s
    """, (student_id,))
    student = cursor.fetchone()
    
    cursor.execute("""
        SELECT name, email, mobile_number, course, year_of_study 
        FROM students 
        WHERE room_id = %s AND id != %s AND status = 'active'
    """, (student['room_id'] if student and student.get('room_id') else 0, student_id))
    roommates = cursor.fetchall()
    
    conn.close()
    return jsonify({
        'student': student,
        'roommates': roommates
    })

@app.route('/api/student/complaints', methods=['GET', 'POST'])
def api_student_complaints():
    student_id = api_require_student()
    if not student_id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        data = request.json
        subject = data.get('subject')
        description = data.get('description')
        if not subject or not description:
            conn.close()
            return jsonify({'error': 'Subject and Description are required'}), 400
        
        cursor.execute("INSERT INTO complaints (student_id, subject, description) VALUES (%s, %s, %s)",
                       (student_id, subject, description))
        conn.commit()
        log_activity(student_id, f"Submitted a new complaint: {subject}")
        conn.close()
        return jsonify({'message': 'Complaint submitted successfully'})
        
    else:
        cursor.execute("SELECT * FROM complaints WHERE student_id = %s ORDER BY submitted_at DESC", (student_id,))
        complaints = cursor.fetchall()
        # Convert datetime to string
        for c in complaints:
            if c.get('submitted_at'): c['submitted_at'] = c['submitted_at'].strftime('%Y-%m-%d %H:%M:%S')
            if c.get('resolved_at'): c['resolved_at'] = c['resolved_at'].strftime('%Y-%m-%d %H:%M:%S')
        conn.close()
        return jsonify(complaints)

@app.route('/api/student/fee_status', methods=['GET'])
def api_student_fee_status():
    student_id = api_require_student()
    if not student_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fees WHERE student_id = %s ORDER BY year DESC, month DESC, id DESC", (student_id,))
    fees = cursor.fetchall()
    for f in fees:
        if f.get('created_at'): f['created_at'] = f['created_at'].strftime('%Y-%m-%d')
    conn.close()
    return jsonify(fees)

@app.route('/api/student/notices', methods=['GET'])
def api_student_notices():
    student_id = api_require_student()
    if not student_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM notices ORDER BY created_at DESC LIMIT 20")
    notices = cursor.fetchall()
    for n in notices:
        if n.get('created_at'): n['created_at'] = n['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    conn.close()
    return jsonify(notices)

@app.route('/api/student/receipts', methods=['GET'])
def api_student_receipts():
    student_id = api_require_student()
    if not student_id:
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM fee_receipts WHERE student_id = %s ORDER BY created_at DESC", (student_id,))
    receipts = cursor.fetchall()
    for r in receipts:
        if r.get('created_at'): r['created_at'] = r['created_at'].strftime('%Y-%m-%d %H:%M:%S')
    conn.close()
    return jsonify(receipts)

# ============================================================
# RUN THE APP
# ============================================================
if __name__ == '__main__':
    create_default_admin()     # Create admin on first run
    app.run(host='0.0.0.0', debug=True, port=5000, use_reloader=False)
