# ROUTE: Self-Registration (Student via QR)
# ============================================================
@app.route('/student-registration', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        mobile_number = request.form.get('mobile_number', '').strip()
        dob = request.form.get('dob') or None
        college_name = request.form.get('college_name', '').strip()
        course = request.form.get('course', '').strip()
        roll_number = request.form.get('roll_number', '').strip() or None
        year_of_study = request.form.get('year_of_study', 1)
        parent_name = request.form.get('parent_name', '').strip()
        parent_number = request.form.get('parent_number', '').strip()
        permanent_address = request.form.get('permanent_address', '').strip()
        city = request.form.get('city', '').strip()
        state = request.form.get('state', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not name or not email or not password:
            flash("Name, email and password are required.", "error")
            return redirect(url_for('student_registration'))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('student_registration'))

        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Check if email is already registered
        cursor.execute("SELECT id FROM students WHERE email = %s", (email,))
        if cursor.fetchone():
            flash(f"Error: The email address '{email}' is already registered.", "error")
            cursor.close(); conn.close()
            return redirect(url_for('student_registration'))

        # Hash the password
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            cursor.execute(
                """INSERT INTO students (name, email, password_hash, mobile_number, parent_number, roll_number, 
course, year_of_study, dob, parent_name, college_name, permanent_address, city, state, status, must_change_password)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', FALSE)""",
                (name, email, hashed, mobile_number, parent_number, roll_number, course, year_of_study, 
                 dob, parent_name, college_name, permanent_address, city, state)
            )
            conn.commit()
            flash("Registration successful! Please wait for the admin to approve your request.", "success")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('student_registration'))

    return render_template('student_registration.html')


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
                           pending_students=pending_students,
                           rooms=rooms,
                           complaints=complaints,
                           notices=notices,
                           fees=fees,
                           sms_logs=sms_logs,
                           sms_settings=sms_settings,
                           sms_analytics=sms_analytics,
                           todays_menu=todays_menu,
                           optouts=optouts,
                           expected_counts=expected_counts,
                           today_str=today_str)

# ============================================================
# ROUTE: Admin Registration Request Accept/Reject
# ============================================================
@app.route('/admin/request/accept/<int:student_id>', methods=['POST'])
def accept_request(student_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401
    
    room_id = request.form.get('room_id')
    if not room_id:
        flash("Room assignment is required to approve the student.", "error")
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # Check if student is still pending
        cursor.execute("SELECT * FROM students WHERE id = %s AND status = 'pending'", (student_id,))
        student = cursor.fetchone()
        if not student:
            flash("Student not found or already processed.", "error")
            cursor.close(); conn.close()
            return redirect(url_for('admin_dashboard'))

        # Check room status
        cursor.execute("SELECT * FROM rooms WHERE id = %s", (room_id,))
        room = cursor.fetchone()
        if not room or room['status'] == 'full':
            flash("Selected room is invalid or full.", "error")
            cursor.close(); conn.close()
            return redirect(url_for('admin_dashboard'))

        # Update student
        cursor.execute("UPDATE students SET status = 'active', room_id = %s WHERE id = %s", (room_id, student_id))

        # Update room occupancy
        cursor.execute("UPDATE rooms SET current_occupancy = current_occupancy + 1 WHERE id = %s", (room_id,))
        cursor.execute("UPDATE rooms SET status = IF(current_occupancy >= capacity, 'full', 'available') WHERE id = %s", (room_id,))

        # Create initial fee
        today = date.today()
        month_name = today.strftime("%B %Y")
        due = today.replace(day=10)
        fee_amount = room['monthly_fee']

        cursor.execute(
            "INSERT INTO fees (student_id, amount, month, year, due_date) VALUES (%s, %s, %s, %s, %s)",
            (student_id, fee_amount, month_name, today.year, due)
        )

        conn.commit()

        # Send welcome email
        login_url = url_for('login', _external=True)
        body = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 10px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 35px 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; letter-spacing: 0.5px;">Chennakesava Boys Hostel</h1>
                <p style="color: #bfdbfe; margin: 10px 0 0 0; font-size: 18px; font-weight: 500;">Registration Approved!</p>
            </div>
            
            <div style="padding: 40px 30px; background-color: #ffffff;">
                <p style="font-size: 16px; color: #374151; margin-top: 0;">Dear <strong>{student['name']}</strong>,</p>
                <p style="font-size: 16px; color: #4b5563; line-height: 1.6; margin-bottom: 25px;">
                    We are pleased to inform you that your registration request for Chennakesava Boys Hostel has been approved by the administration.
                </p>
                <p style="font-size: 16px; color: #4b5563; line-height: 1.6; margin-bottom: 30px;">
                    You have been assigned to <strong>Room {room['room_number']}</strong>.
                    You can now log in to the student portal using your registered email and the password you created during registration.
                </p>
                
                <div style="text-align: center; margin: 40px 0 10px 0;">
                    <a href="{login_url}" style="background-color: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 35px; border-radius: 6px; font-weight: 600; font-size: 16px; display: inline-block; box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2); transition: all 0.3s ease;">Log in to Portal</a>
                </div>
            </div>
        </div>
        """
        send_auth_email(student['email'], "Hostel Registration Approved!", body)

        flash(f"Student {student['name']} approved and assigned to Room {room['room_number']}.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error processing request: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/request/reject/<int:student_id>', methods=['POST'])
def reject_request(student_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE students SET status = 'rejected' WHERE id = %s AND status = 'pending'", (student_id,))
        conn.commit()
        flash("Registration request rejected.", "info")
    except Exception as e:
        conn.rollback()
        flash(f"Error rejecting request: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('admin_dashboard'))

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
    

def run_migrations():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE students MODIFY COLUMN status ENUM('active', 'inactive', 'pending', 'rejected') DEFAULT 'active';")
        conn.commit()
        cursor.close()
        conn.close()
        print("Database migrations applied successfully.")
    except Exception as e:
        print(f"Migration info (already applied or error): {e}")

# ============================================================
# RUN THE APP
# ============================================================
if __name__ == '__main__':
    run_migrations()           # Run DB schema migrations
    create_default_admin()     # Create admin on first run
    app.run(host='0.0.0.0', debug=True, port=5000, use_reloader=False)
