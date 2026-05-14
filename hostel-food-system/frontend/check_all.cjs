const puppeteer = require('puppeteer');

(async () => {
    try {
        const browser = await puppeteer.launch({ headless: 'new' });
        const page = await browser.newPage();
        
        page.on('console', msg => {
            console.log(`[CONSOLE ${msg.type()}] ${msg.text()}`);
        });
        
        page.on('pageerror', err => {
            console.log(`[PAGE ERROR] ${err.toString()}`);
        });

        console.log("Checking React App...");
        await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' }).catch(e => console.log("Failed to load React app"));
        await new Promise(r => setTimeout(r, 2000));
        
        console.log("Attempting to log into React App...");
        try {
            await page.type('input[type="email"]', 'student@hostel.com');
            await page.type('input[type="password"]', 'student123');
            await page.click('button'); // Login button has no type="submit"
            
            // Wait for navigation or network requests
            await new Promise(r => setTimeout(r, 4000));
            console.log("Checked React App Dashboard.");
        } catch (e) {
            console.log("Could not login:", e.message);
        }

        await browser.close();
    } catch (e) {
        console.error("Puppeteer script failed:", e);
    }
})();
