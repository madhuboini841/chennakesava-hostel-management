import os
import requests

def generate_qr():
    # We will just point it to a placeholder domain or relative path for now.
    # In production, they should print a QR code with the actual domain.
    # Let's point it to the generic path or a sample production URL
    target_url = "https://chennakesava-hostel-management.onrender.com/student-registration"
    
    img_dir = os.path.join(os.path.dirname(__file__), 'static', 'img')
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, 'qr_registration.png')
    
    api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={target_url}"
    
    print(f"Generating QR Code for: {target_url}")
    response = requests.get(api_url)
    
    if response.status_code == 200:
        with open(img_path, 'wb') as f:
            f.write(response.content)
        print(f"QR Code successfully saved to {img_path}")
    else:
        print(f"Failed to generate QR Code. Status: {response.status_code}")

if __name__ == "__main__":
    generate_qr()
