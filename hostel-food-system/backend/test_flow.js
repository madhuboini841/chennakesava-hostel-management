const BASE_URL = 'http://localhost:5001/api';
let adminToken = '';
let studentToken = '';
let tempPassword = '';
const testEmail = `test_${Date.now()}@hostel.com`;
const newPassword = 'newsecure123';
const resetPassword = 'evennewerpassword123';

async function request(endpoint, body = null, token = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    
    const res = await fetch(`${BASE_URL}${endpoint}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
}

async function runTests() {
    try {
        console.log('--- Starting Authentication Flow Tests ---');

        // 1. Admin Login
        console.log('\n1. Testing Admin Login...');
        const adminRes = await request('/auth/login', {
            email: 'admin@hostel.com',
            password: 'admin123'
        });
        adminToken = adminRes.token;
        console.log('✅ Admin Login Successful');

        // 2. Student Registration
        console.log('\n2. Testing Student Registration...');
        const regRes = await request('/admin/register-student', {
            name: 'API Test Student',
            email: testEmail,
            meal_preference: 'veg'
        }, adminToken);
        
        console.log('Registration Response:', regRes.message);
        const match = regRes.message.match(/manually: ([a-z0-9]+)$/);
        if (!match) throw new Error("Could not extract temp password");
        tempPassword = match[1];
        console.log('✅ Student Registration Successful. Temp Password:', tempPassword);

        // 3. Student Login with Temp Password
        console.log('\n3. Testing Student Login with Temp Password...');
        const studentRes1 = await request('/auth/login', {
            email: testEmail,
            password: tempPassword
        });
        studentToken = studentRes1.token;
        console.log('✅ Student Login Successful');

        // 4. Change Password
        console.log('\n4. Testing Change Password...');
        await request('/auth/change-password', {
            currentPassword: tempPassword,
            newPassword: newPassword
        }, studentToken);
        console.log('✅ Change Password Successful');

        // 5. Student Login with New Password
        console.log('\n5. Verifying Login with New Password...');
        await request('/auth/login', {
            email: testEmail,
            password: newPassword
        });
        console.log('✅ Login with New Password Successful');

        // 6. Forgot Password
        console.log('\n6. Testing Forgot Password...');
        const forgotRes = await request('/auth/forgot-password', {
            email: testEmail
        });
        console.log('Forgot Password Response:', forgotRes.message);
        const urlMatch = forgotRes.message.match(/link: (http.*)$/);
        if (!urlMatch) throw new Error("Could not extract reset link");
        const resetUrl = new URL(urlMatch[1]);
        const resetToken = resetUrl.pathname.split('/').pop();
        console.log('✅ Forgot Password Successful. Reset Token extracted:', resetToken);

        // 7. Reset Password
        console.log('\n7. Testing Reset Password...');
        await request('/auth/reset-password', {
            token: resetToken,
            email: testEmail,
            newPassword: resetPassword
        });
        console.log('✅ Reset Password Successful');

        // 8. Final Login Verification
        console.log('\n8. Verifying Login with Reset Password...');
        await request('/auth/login', {
            email: testEmail,
            password: resetPassword
        });
        console.log('✅ Final Login Successful!');

        console.log('\n🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉');

    } catch (err) {
        console.error('\n❌ TEST FAILED!');
        console.error(err);
    }
}

runTests();
