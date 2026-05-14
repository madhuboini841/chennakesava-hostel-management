const puppeteer = require('puppeteer');

(async () => {
    try {
        const browser = await puppeteer.launch({ headless: 'new' });
        const page = await browser.newPage();
        
        page.on('console', msg => {
            if (msg.type() === 'error') {
                console.log(`PAGE ERROR: ${msg.text()}`);
            }
        });
        
        page.on('pageerror', err => {
            console.log(`PAGE EXCEPTION: ${err.toString()}`);
        });

        // Navigate to the student dashboard
        await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' });
        
        // Wait a bit to see if there are any immediate errors
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        console.log("Done checking login page.");
        
        await browser.close();
    } catch (e) {
        console.error("Puppeteer script failed:", e);
    }
})();
