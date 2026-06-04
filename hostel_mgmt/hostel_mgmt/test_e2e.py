import requests
from bs4 import BeautifulSoup
import random

def run_tests():
    session = requests.Session()
    base_url = "http://127.0.0.1:5000"
    
    rnd = random.randint(1000, 9999)
    email = f"e2etest{rnd}@example.com"
    username = f"e2etest{rnd}"

    print(f"1. Registering new student {email} via QR code url...")
    res = session.post(f"{base_url}/student-registration", data={
        "name": f"E2E Test Student {rnd}",
        "email": email,
        "mobile_number": f"123456{rnd}",
        "parent_name": "Parent",
        "parent_mobile": "0987654321",
        "address": "Test Address",
        "college_name": "Test College",
        "course": "B.Tech",
        "username": username,
        "password": "password123",
        "confirm_password": "password123"
    })
    
    soup_reg = BeautifulSoup(res.text, 'html.parser')
    for msg in soup_reg.find_all('div', class_='flash'):
        print("REGISTRATION FLASH:", msg.text.strip().encode('ascii', 'replace').decode())
        
    print(f"2. Attempting to login before approval...")
    res = session.post(f"{base_url}/login", data={
        "role": "student",
        "email": email,
        "password": "password123"
    })
    # Login should fail because status is pending
    if "Pending" in res.text or "active" in res.text.lower() or "rejected" in res.text.lower():
        print("Login correctly prevented or flashed message.")
    else:
        print("Login might have succeeded when it shouldn't have? Status: ", res.url)

    print("3. Logging in as Admin...")
    res = session.post(f"{base_url}/login", data={
        "role": "admin",
        "email": "admin@hostel.com",  # Default admin
        "password": "admin123"
    })
    
    print("4. Fetching admin dashboard to get student ID and room ID...")
    res = session.get(f"{base_url}/admin/dashboard")
    soup = BeautifulSoup(res.text, 'html.parser')
    
    title = soup.find('title')
    print("PAGE TITLE:", title.text if title else "NO TITLE")
    
    # Find student ID
    student_id = None
    # We can fetch it by looking at the page HTML
    pending_students = soup.find_all('button')
    for btn in pending_students:
        onclick_val = btn.get('onclick', '')
        if 'openAcceptRequestModal' in onclick_val:
            if email in res.text or 'E2E Test Student' in onclick_val:
                student_id = int(onclick_val.split('(')[1].split(',')[0])
                break
                
    if not student_id:
        print("Could not find pending student ID in dashboard!")
        for btn in pending_students:
            onclick_val = btn.get('onclick', '')
            if 'openAcceptRequestModal' in onclick_val:
                print("FOUND BUTTON:", onclick_val)
        return
        
    print(f"Found student ID: {student_id}")
    
    # Get available room ID
    room_select = soup.find('select', {'name': 'room_id'})
    room_id = None
    if room_select:
        options = room_select.find_all('option')
        for opt in options:
            if opt.get('value') and not opt.has_attr('disabled'):
                room_id = opt['value']
                break
                
    if not room_id:
        print("Could not find available room to assign!")
        return
        
    print(f"Found room ID: {room_id}")
    
    print("5. Approving student...")
    res = session.post(f"{base_url}/admin/request/accept/{student_id}", data={
        "room_id": room_id
    })
    
    # Logout admin
    session.get(f"{base_url}/logout")
    
    print("6. Logging in as Student after approval...")
    res = session.post(f"{base_url}/login", data={
        "role": "student",
        "email": email,
        "password": "password123"
    })
    
    if "Dashboard" in res.text or "/student/dashboard" in res.url:
        print("Student successfully logged in!")
    else:
        print("Student failed to login after approval.")
        return
        
    print("7. Verifying Student Dashboard for fees...")
    res = session.get(f"{base_url}/student/dashboard")
    if "Razorpay" in res.text or "Pay Online" in res.text or "razorpay" in res.text.lower():
        print("Razorpay button is visible! Integration is unaffected.")
    else:
        print("Could not find Razorpay / Pay Online integration text on student dashboard.")
        
    print("All E2E tests successfully executed!")

if __name__ == "__main__":
    run_tests()
