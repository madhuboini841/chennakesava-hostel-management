const nodemailer = require('nodemailer');
require('dotenv').config();

const transporter = nodemailer.createTransport({
    host: 'smtp-mail.outlook.com',
    port: 587,
    secure: false, // true for 465, false for other ports
    auth: {
        user: process.env.EMAIL_USER,
        pass: process.env.EMAIL_PASS,
    },
    tls: {
        ciphers: 'SSLv3'
    }
});

// Verify SMTP connection on startup
transporter.verify((error, success) => {
    if (error) {
        console.error('Nodemailer SMTP Connection Error:', error.message);
        console.log('Please check your EMAIL_USER and EMAIL_PASS in the .env file.');
    } else {
        console.log('Nodemailer SMTP Connection Successful. Ready to send emails.');
    }
});

// Generic reusable email sending function
const sendEmail = async ({ to, subject, html }) => {
    try {
        const mailOptions = {
            from: process.env.EMAIL_USER,
            to,
            subject,
            html
        };
        const info = await transporter.sendMail(mailOptions);
        console.log(`Email sent successfully to ${to}. Message ID: ${info.messageId}`);
        return info;
    } catch (error) {
        console.error(`Failed to send email to ${to}:`, error.message);
        throw error;
    }
};

const sendRegistrationEmail = async (email, password) => {
    try {
        const loginUrl = process.env.FRONTEND_URL || 'http://localhost:5173';
        const mailOptions = {
            from: process.env.EMAIL_USER,
            to: email,
            subject: 'Welcome to Hostel Food System - Your Login Credentials',
            html: `
                <h3>Welcome to the Hostel Food System!</h3>
                <p>Your account has been created by the administrator.</p>
                <p><strong>Email:</strong> ${email}</p>
                <p><strong>Temporary Password:</strong> ${password}</p>
                <br>
                <p>Please log in using the link below and change your password as soon as possible.</p>
                <a href="${loginUrl}">Log In Here</a>
            `
        };
        await transporter.sendMail(mailOptions);
        console.log(`Registration email sent to ${email}`);
    } catch (error) {
        console.error('Error sending registration email:', error);
        throw error;
    }
};

const sendPasswordResetEmail = async (email, resetUrl) => {
    try {
        const mailOptions = {
            from: process.env.EMAIL_USER,
            to: email,
            subject: 'Password Reset Request',
            html: `
                <h3>Password Reset Request</h3>
                <p>We received a request to reset your password for the Hostel Food System.</p>
                <p>Click the link below to reset your password. This link is valid for 1 hour.</p>
                <a href="${resetUrl}">Reset Password</a>
                <br>
                <p>If you did not request this, please ignore this email.</p>
            `
        };
        await transporter.sendMail(mailOptions);
        console.log(`Password reset email sent to ${email}`);
    } catch (error) {
        console.error('Error sending password reset email:', error);
        throw error;
    }
};

module.exports = {
    sendRegistrationEmail,
    sendPasswordResetEmail,
    sendEmail
};
