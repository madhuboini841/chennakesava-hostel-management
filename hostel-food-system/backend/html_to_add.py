          <li class="nav-item"><a href="#requests" class="nav-link" onclick="showSection('requests', this)"><span class="nav-icon">📋</span> Registration Requests {% if pending_students %}<span class="sidebar-badge" style="display:inline-block; background:var(--danger)">{{ pending_students|length }}</span>{% endif %}</a></li>
          <li class="nav-item"><a href="#students" class="nav-link" onclick="showSection('students', this)"><span class="nav-icon">👨‍🎓</span> Students</a></li>


        <!-- ===== SECTION: REGISTRATION REQUESTS ===== -->
        <div id="section-requests" class="dashboard-section" style="display:none">
          
          <!-- Registration QR Card -->
          <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
              <div class="card-title">📱 Student Registration QR</div>
            </div>
            <div class="card-body" style="padding: 20px; display: flex; flex-direction: column; align-items: center; gap: 15px; text-align: center;">
              <p style="color: #64748b; font-size: 14px; max-width: 500px;">
                Students can scan this QR code to self-register for the hostel. Their requests will appear below for your approval.
              </p>
              <div style="background: white; padding: 15px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <img src="/static/img/qr_registration.png" alt="Registration QR Code" style="width: 200px; height: 200px; border-radius: 8px;">
              </div>
              <div style="display: flex; gap: 10px; margin-top: 10px;">
                <a href="/static/img/qr_registration.png" download="registration_qr.png" class="btn btn-sm btn-accent" style="text-decoration: none;">
                  📥 Download QR
                </a>
                <button class="btn btn-sm" style="background: #e2e8f0; color: #1e293b; border: none; cursor: pointer;" onclick="copyRegistrationLink()">
                  🔗 Copy Registration Link
                </button>
              </div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="card-title">📋 Student Registration Requests</div>
            </div>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr><th>Name</th><th>Email & Phone</th><th>Course</th><th>Applied On</th><th>Actions</th></tr>
                </thead>
                <tbody>
                  {% for s in pending_students %}


      <div class="modal-header">
        <h3>Approve Registration Request</h3>
        <button class="close-btn" onclick="closeModal('acceptRequestModal')">✕</button>
      </div>
      <div class="modal-body">
        <p style="margin-bottom: 15px;">Assign a room to <strong><span id="acceptStudentName"></span></strong> to complete the registration.</p>
        <form id="acceptRequestForm" method="POST" action="">
          <div class="form-group">
            <label>Assign Room *</label>
            <select name="room_id" required>
              <option value="">— Select a room —</option>
              {% for r in rooms %}
              <option value="{{ r.id }}" {% if r.status == 'full' %}disabled{% endif %}>
                Room {{ r.room_number }} — {{ r.room_type|title }}, Floor {{ r.floor }}
                ({{ r.current_occupancy }}/{{ r.capacity }} occupied, ₹{{ "%.0f"|format(r.monthly_fee) }}/month)
                {% if r.status == 'full' %} [FULL]{% endif %}
              </option>
              {% endfor %}


      } catch (err) {
        alert("Error sending Test SMS: " + err);
      }
    }

    function copyRegistrationLink() {
      const url = window.location.origin + '/student-registration';
      navigator.clipboard.writeText(url).then(() => {
        alert("Registration link copied to clipboard: " + url);
      }).catch(err => {
        console.error('Failed to copy link: ', err);
        alert("Could not copy link automatically. URL is: " + url);
      });
    }
  </script>
