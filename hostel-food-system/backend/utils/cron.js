const cron = require('node-cron');
const { run } = require('../db');

function initCronJobs() {
    // 1. Lock Breakfast Menu daily at 7:00 AM
    cron.schedule('0 7 * * *', async () => {
        const today = new Date().toISOString().split('T')[0];
        try {
            await run("UPDATE daily_menus SET is_locked = 1 WHERE date = ? AND meal_slot = 'breakfast'", [today]);
            console.log(`[CRON] Locked breakfast menus for ${today}`);
        } catch (err) {
            console.error('[CRON] Error locking breakfast menus', err);
        }
    });

    // 2. Lock Lunch & Dinner Menu daily at 10:00 AM
    cron.schedule('0 10 * * *', async () => {
        const today = new Date().toISOString().split('T')[0];
        try {
            await run("UPDATE daily_menus SET is_locked = 1 WHERE date = ? AND meal_slot IN ('lunch', 'dinner')", [today]);
            console.log(`[CRON] Locked lunch/dinner menus for ${today}`);
        } catch (err) {
            console.error('[CRON] Error locking lunch/dinner menus', err);
        }
    });

    // 3. Daily 8:00 AM Reminder Notification to Students
    cron.schedule('0 8 * * *', async () => {
        try {
            const today = new Date().toISOString().split('T')[0];
            const msg = `Check today's (${today}) menu! If you are not eating, opt out before 10 AM.`;

            await run(
                "INSERT INTO notifications (user_id, message) SELECT id, ? FROM users WHERE role = 'student' AND is_active = 1",
                [msg]
            );
            console.log('[CRON] Sent 8 AM reminders to students.');
        } catch (err) {
            console.error('[CRON] Error sending reminders', err);
        }
    });
}

module.exports = initCronJobs;
