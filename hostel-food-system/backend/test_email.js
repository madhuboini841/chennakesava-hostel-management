require('dotenv').config();
const { sendEmail } = require('./utils/email');

// The destination email address to test sending TO
// We default to the EMAIL_USER so it sends an email to itself
const testRecipient = process.env.EMAIL_USER;

console.log('--- Starting Email Test ---');

if (!process.env.EMAIL_USER || process.env.EMAIL_USER.includes('your_outlook_email')) {
    console.error('ERROR: You must configure EMAIL_USER and EMAIL_PASS in backend/.env before running this test.');
    process.exit(1);
}

const runTest = async () => {
    try {
        console.log(`Attempting to send a test email to: ${testRecipient}`);
        
        await sendEmail({
            to: testRecipient,
            subject: 'Test Email from Hostel Food System',
            html: `
                <h2>Test Email Successful!</h2>
                <p>If you are receiving this, your Nodemailer Outlook SMTP configuration is working perfectly.</p>
                <p>This confirms that your backend can now send automated emails to students and administrators.</p>
                <br>
                <p>Time Sent: ${new Date().toLocaleString()}</p>
            `
        });
        
        console.log('--- Test Completed Successfully ---');
        process.exit(0);
    } catch (error) {
        console.error('--- Test Failed ---');
        console.error(error.message);
        process.exit(1);
    }
};

// Wait a brief moment for the Nodemailer transporter.verify() to print its status
setTimeout(runTest, 1000);
